# Banking Trust Score System – Project Flow Documentation

###### Please read this carefully!

## Overview

This backend system calculates a **trust score** for each user based on their behavior (transactions, device usage, etc.). The score determines which **user level** they belong to and what **restrictions** are applied to them.

---

## Flow Explanation

### 1. User Registration Flow

- When a user creates an account:
  - They are assigned a **default trust score of 100**.
  - User data is saved into **MongoDB**.
  - A corresponding **user node is created in Neo4j**.


### 2. Login Flow

- When a user logs in:
  - The system checks **Redis cache** to see if the score exists.
    - If **yes**, it uses the score from Redis.
    - If **no**, it fetches the score from MongoDB.
  
```python
def get_score(user_id: str) -> int:
    score = redis.get_or_load_score(user_id, mongo.get_score)
    return score if score is not None else 0
```

- If the user has a **score below 30**, they are **blocked immediately** and prompted to verify their identity.

```json
{
    "error": "Account is locked. Identity verification required"
}
```

- If the score is **30 or higher**, the login succeeds, and the user receives a message showing:
  - Their **current level**
  - Their **active limitations**

```json
{
    "flag": "Normal",
    "message": "Login successful",
    "score": 80,
    "user_email": "test.user@gmail.com",
    "warning": "You can make transactions up to €5,000 in 3 months"
}
```


### 3. Transaction Flow

- When a user tries to **make a transaction**:
  - The system first checks the **trust policy** based on their score.

```python
def make_transaction():
    ...
    try:
        enforce_trust_policy(
            user_id=txn.sender.user_id,
            mongo_model=mongo_txn_model,
            amount=txn.amount,
            action="transaction"
        )
    except HTTPException as e:
        return {"error": "Transaction blocked by trust policy", "details": str(e)}, 403
    ...
```
  - If they **violate any rule**, the transaction is **blocked immediately** with a message explaining why.
  - If allowed:
    - A transaction ID is generated.
    - The transaction is executed.
    - Transaction data is saved into both **MongoDB** and **Neo4j**.
    - **Trust score is recalculated** right after the transaction.


### 4. Score Flow

- Score is **only updated** when:
  - A user **makes a transaction**
  - A user **explicitly requests score recalculation**
> ⚠️ **Note:**  
>  Score is **not recalculated during login** to keep login fast and avoid delays.
- When score is recalculated:
  1. It is **updated in Redis first**
  2. Then **MongoDB fetches the value from Redis** and updates its copy to ensure consistency

```python
def calculate_score(user_id: str, transaction_id=None) -> tuple[int, set[str]]:
    ...

    redis.update_score(user_id, score)

    if newly_applied_rules:
        mongo_user.append_deductions(user_id, list(newly_applied_rules))
    ...

def update_score_mongo(user_id: str, old_score: Optional[int] = None):
    if old_score is None:
        old_score = mongo.get_score(user_id)
    new_score = redis.get_score(user_id)
    if new_score is not None and old_score != new_score:
        mongo.update_score(user_id, new_score)
        return "Score updated successfully in MongoDB"
```

- On future logins or score checks:
  - The system reads from **Redis (if available)** or **MongoDB (fallback)**

---

## Score Recalculation Behavior

### Can score be reduced multiple times for the same issue?

- **Yes**, for these issues:
  - **High transaction amount**
  - **Circular transactions**
  
  These can happen multiple times and should lead to multiple penalties.

- **No**, for other issues like:
  - Sharing devices
  - Having too many devices
  - These are logged once per user. The system uses a list called `score_deductions_applied` in MongoDB to track which penalty types have already been applied. These will **not** reduce the score again if already logged.

---

### Flow of Score Recalculation

1. **Violation Scanning Phase**:
   - Each time a score recalculation is triggered (either after a transaction or via an explicit API call), the system will scan through all predefined rules.
   - For each rule, it checks whether the user currently violates it.

2. **Logging Violations**:
   - If a new violation is detected, it will be added to the `score_deductions_applied` list in MongoDB.
   - This ensures that the same issue won’t trigger repeated penalties unless it’s a rule that allows multiple hits (e.g., high amount or circular).

```python
def log_suspicious_actions(user_id, transaction_id=None):
    log = set()

    # check suspicious transactions amount
    if check_high_transactions_amount(user_id, transaction_id):
        log.add('high_txn_amount')

    # check suspicious monthly spending
    if check_suspicious_monthly_spent(user_id):
        log.add('high_monthly_spent')

    # check new account status
    if is_new_account(user_id):
        log.add('new_account')
    ...
```

3. **Score Calculation Phase**:
   - After violation logging, the `calculate_score()` function is called.
   - This function reduces the user’s score according to the list of currently violated rules.
   - Some deductions are one-time only, others are cumulative depending on the violation type.

This structure allows the system to maintain fairness and avoid over-penalizing users for the same behavior, while still catching repeated risky activities.

---

## NoSQL integration explanation

#### 1. Mongodb:

MongoDB is used for storing document-based data such as transactions, devices, and logs.

**Use Cases:**
- Aggregation pipelines to analyze monthly user spending and detect anomalies compared to previous months.
- Lookup of devices linked to a specific user and vice versa.
- Efficient filtering and projection for lightweight data retrieval.

**Where are them?**

- services/suspicious_service.py
`def check_suspicious_monthly_spent(user_id):`

- services/mongo_service.py
`def get_users_by_device(self, device_id):`
`def get_devices_by_user(self, user_id):`

#### 2. Neo4j:
Neo4j powers the detection of graph-based fraud patterns.

**Use Cases:**
- Path traversal queries to identify circular transaction flows between users.
- Helps detect suspicious money laundering behavior by analyzing user–transaction–user cycles within a short time frame.

**Where is it?**
- services/suspicious_service.py
`def detect_circular_transaction(self, tx_data):`

#### 3. Redis

Redis is used for high-performance caching.

**Use Cases:**
- Caching trust scores (`user_id` → `score`) to reduce recomputation.
- Stored as string values with a TTL of 1 hour.
- Improves system responsiveness for repeated checks.

---

## Summary

| Database | Purpose                                    |
|----------|--------------------------------------------|
| MongoDB  | Document storage and data aggregation      |
| Neo4j    | Graph analysis and fraud path detection    |
| Redis    | Caching trust scores for faster access     |
---

### Okay so that was the flow and I understand what is going on now but does it work?

**Yes!** Check out the test cases and the test reports in the doc folder.

```bash
└── doc
    ├── authentication_test.md
    ├── suspicious_detect_and_score_test.md
    └── transaction_policy_test.md
```

I also prepared a postman collection for testing endpoints

---

## Questions that might be in your mind


#### 1. How can a user reset their score?

- **Currently not supported**.
- This is a **Minimum Viable Product (MVP)** and focuses only on core suspicious behavior detection.


#### 2. Why update the score in Redis first?

- Redis is used for **fast lookups**.
- Redis has a **Time To Live (TTL) of 1 hour**.
- If Redis is not updated after a penalty, the cached score will become outdated and **out of sync** with MongoDB, leading to **inconsistent behavior**.

#### 3. What are the uses cases of this project?

- **Fraud detection**: Block transactions that exceeds limits in real-time.
- **Access control**: Restrict features based on trust score.
- **User classification**: Group users into Trusted, Risky, etc.
- **Policy enforcement**: Enforce transaction limits and behavior rules.
- **Risk analytics**: Log violations to analyze risky patterns.
- **Microservice integration**: Plug into larger platforms (e.g., fintech, e-commerce).

#### 4. Does this app have frontend?

- **Yes!** Check out the fontend folder and read the README.md
- But still, the system logic is **complex** with many edge cases so we focused on:
  - **Comprehensive integration test cases**
  - **Postman collections** to test all logic and API flows tightly
- If you wanna see how this app behaves, we recommend to use **postman collections** or checkout the **test cases** because testing with frontend might be slower and harder.


#### 5. Is AI used in this project?

- **Yes, absolutely**, AI tools were used **as mentors**, not as code writers.
- We used them for suggestions, logic reviews, and debugging assistance.
- We tried to not to use AI as much as we can so if there are places in the code that are not optimal, please know that **we did our best** and wrote everything ourselves.

---

## Future Improvements

- Add **Reset Score** feature for users or admins.
- Add **Verify Identity** feature for users with trust score below 30.

---

Thank you for reading, if you have any questions, feel free to reach us so we can discuss about it!
