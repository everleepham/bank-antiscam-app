TRUST_POLICY = [
    {
        "min": 90,
        "max": 100,
        "level": "trusted",
        "restrictions": None
    },
    {
        "min": 75,
        "max": 89,
        "level": "normal",
        "restrictions": {
            "total_amount_limit": 5000,
            "window_months": 3
        }
    },
    {
        "min": 50,
        "max": 74,
        "level": "risky",
        "restrictions": {
            "max_high_value_txns": 10,
            "threshold": 1000,
            "window_months": 3
        }
    },
    {
        "min": 30,
        "max": 49,
        "level": "fraud_prone",
        "restrictions": {
            "max_txns_per_month": 10,
            "max_txn_amount": 100
        }
    },
    {
        "min": 0,
        "max": 29,
        "level": "critical",
        "restrictions": {
            "locked": True
        }
    }
]
