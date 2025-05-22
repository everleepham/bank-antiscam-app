# Blacklist Intelligence & Trust Score System for Web Services

## Team Members
- Debojyoti Mishra  
- Phuong Khanh Pham

---

## Description
A real-time trust engine for web applications (e.g. banking portal) that flags malicious users based on:
- Behavior patterns
- Relationships
- Metadata

The system makes **split-second decisions** on user access levels.

## Why a Banking Portal?
- **High-stakes data**: financial info, personal data
- **Real-world fraud detection**
- Simulate trust decisions like:
  - Flagging unusual transactions
  - Locking accounts on suspicious logins
  - Requiring 2FA for certain actions
- **Rich metadata**: location, device, time, transaction patterns

---

## Databases Used

#### Neo4j
- Maps user relationships, IPs, device fingerprints, behavior
- Detects patterns like:
  - Shared devices/IPs
  - Botnets and sock puppets
  - Suspicious user networks

#### MongoDB
- Stores raw logs and semi-structured data:
  - Login attempts
  - Device/browser data
  - User history and flags
  - User-uploaded content

#### Redis
- Real-time scoring and blacklist decisioning
- Caching known results
- Queueing behavior events

---

## Scenario Example
1. User logs in  
2. **Redis** fetches cached trust score (FAST). If borderline:
3. **MongoDB** provides raw metadata  
4. **Neo4j** checks user’s network links  
5. If user is linked (e.g. 3 hops from a known bot), access is restricted  
6. Redis updates trust score → future calls blocked instantly  

---

## Trust Scoring Flow

1. **User Logs In**
   - Sends device, IP, username to backend

2. **Redis Checks Trust Score**
   - If cached, returns immediately  
   - Otherwise, proceed to MongoDB

3. **MongoDB Logs User Info**
   - Stores login data, profile, device/browser, location

4. **Neo4j Evaluates User Connections**
   - Example query:
     ```cypher
     MATCH (a:User)-[:SHARED_IP_WITH]-(b:User {blacklisted: true}) RETURN a
     ```

5. **Trust Score Calculated (Rule-Based)**
   - Suspicious connection → −20 pts  
   - New account → −10 pts  
   - Same IP/MAC as 5+ users → −30 pts  
   - If the user logins from a different country → -30 pts
   - Spend >2x average → −30 pts  
     - *Can be recovered if justified*

   - Final score stored in Redis for ultra-fast lookup

6. **Limitations based on Trust Score**

| Score     | Description                               | Limitations                                  |
|-----------|-------------------------------------------|----------------------------------------------|
| 90 – 100  | Trusted user                              | No restrictions                              |
| 75 – 89   | Normal user                               | Max €5,000 total in 3 months                 |
| 50 – 74   | Risky user                                | Max 10 transactions > €1,000 in 3 months     |
| 30 – 49   | Fraud-prone user                          | Max 10 transactions/month, each < €100       |
| **< 30**  | **Critical – Account temporarily locked** | No transactions allowed, identity verification required |


---

## Future Improvements
- Transition from rule-based to ML-based scoring
- Visualization of trust graphs
- Admin dashboard with alerts and logs
