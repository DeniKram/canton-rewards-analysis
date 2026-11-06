"""Which endpoints to download for the article. One job = one API call = 1 credit.

(name, path, params, why we need it)
"""
JOBS = [
    # --- Section 1: rewards and the CIP-0096 "liveness cliff"
    ("liveness_cliff_all", "/api/v1/analytics/liveness-cliff", {"period": "all"},
     "daily liveness rewards and number of validators receiving them, before/after the cliff"),
    ("reward_activity_all", "/api/v1/reward-activity", {"period": "all"},
     "network reward volume over time by reward type (app / validator / SV)"),
    ("reward_stats", "/api/v1/reward-stats", None,
     "reward distribution by type for 24h/7d/30d/6m/all"),
    ("mint_burn_all", "/api/v1/analytics/mint-burn", {"period": "all"},
     "daily mint split: application, SV, validator, dev fund"),

    # --- Section 2: Super Validators (actual on-chain weights vs CIP announcements)
    ("sv_rights", "/api/v1/sv-rights", None,
     "actual SV reward weights per owner and node"),
    ("sv_locking", "/api/v1/sv-locking", None,
     "SV tiers, locked balances and compliance"),

    # --- Section 3: validators
    ("validators_balances", "/api/v1/validators/balances", None,
     "every validator and SV: balance, liveness state, sponsor"),

    # --- Section 4: featured apps
    ("fa_compliance_30d", "/api/v1/analytics/featured-apps-compliance", {"period": "30d"},
     "reward weight vs allowed weight vs USD spent, per provider"),
    ("app_economics_30d", "/api/v1/analytics/app-economics", {"period": "30d"},
     "app rewards, sync fees and profit per application"),
    ("fa_locking", "/api/v1/fa-locking", None,
     "CIP-0116 locks per featured app and shortfalls"),

    # --- Context: price and network usage
    ("cc_price_1y", "/api/v1/analytics/cc-price", {"period": "1y"},
     "CC price history to convert CC to USD"),
    ("traffic_burn_all", "/api/v1/analytics/traffic-burn", {"period": "all"},
     "traffic bought and CC burned per day (real usage)"),
]
