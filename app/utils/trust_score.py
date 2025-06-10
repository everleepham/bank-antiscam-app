SCORE = [
    {
        "min": 90,
        "max": 100,
        "flag": "Trusted",
        "warning": None
    },
    {
        "min": 75,
        "max": 89,
        "flag": "Normal",
        "warning": "You can make transactions up to €5,000 in 3 months",
    },
    {
        "min": 50,
        "max": 74,
        "flag": "Risky",
        "warning": "You can make up to 3 transactions over €1,000 in 1 month",
    },
    {
        "min": 30,
        "max": 49,
        "flag": "Fraud Prone",
        "warning": "You can make up to 10 transactions per month, each under €100",
    },
    {
        "min": 0,
        "max": 29,
        "flag": "Critical",
        "warning": "Your account is locked. Identity verification required",
    }
]
