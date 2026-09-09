"""
Generates a deliberately messy, realistic CRM export — mimicking what a
Sales Ops analyst actually receives from MS Dynamics / Salesforce before
cleanup: duplicate accounts, missing DUNS numbers, inconsistent stage
naming, stale opportunities, unconverted leads.

Output: raw/accounts.csv, raw/reps.csv, raw/opportunities.csv
"""
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

OUT = "raw"
import os
os.makedirs(OUT, exist_ok=True)

TODAY = datetime(2026, 9, 1)

# ---------------------------------------------------------------- reps
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
reps = []
for i in range(1, 19):
    reps.append({
        "rep_id": f"R{i:03d}",
        "rep_name": fake.name(),
        "region": random.choice(REGIONS),
        "team": random.choice(["Enterprise", "Mid-Market", "SMB"]),
    })
reps_df = pd.DataFrame(reps)
reps_df.to_csv(f"{OUT}/reps.csv", index=False)

# ------------------------------------------------------------ accounts
INDUSTRIES = ["Manufacturing", "Healthcare", "Financial Services", "Retail",
              "Technology", "Energy", "Telecom", "Public Sector"]

def messy_name_variant(name):
    """Simulate how the same account ends up entered multiple ways."""
    variants = [
        name,
        name.upper(),
        name + " Inc.",
        name.replace("Inc.", "").strip() + " Incorporated",
        name + "  ",  # trailing whitespace
        name.replace(" ", "  "),  # double space
    ]
    return random.choice(variants)

base_companies = [fake.company().replace(",", "") for _ in range(140)]
accounts = []
acct_counter = 1
duplicate_pool = []  # account_ids that will get a duplicate entry

for base in base_companies:
    acct_id = f"A{acct_counter:04d}"
    has_duns = random.random() > 0.28          # ~28% missing DUNS
    created = (TODAY - timedelta(days=random.randint(30, 1095))).date()
    accounts.append({
        "account_id": acct_id,
        "account_name": base,
        "industry": random.choice(INDUSTRIES),
        "country": fake.country(),
        "duns_number": (f"{random.randint(10**8,10**9-1)}" if has_duns else ""),
        "created_date": created,
        "owner_rep_id": random.choice(reps_df.rep_id),
        "account_source": random.choice(["Inbound", "Outbound", "Partner", "Event", ""]),
    })
    acct_counter += 1
    if random.random() < 0.16:  # ~16% of accounts get a messy duplicate record
        duplicate_pool.append((base, acct_id))

# inject duplicate account records (same real company, different account_id)
for base, orig_id in duplicate_pool:
    acct_id = f"A{acct_counter:04d}"
    accounts.append({
        "account_id": acct_id,
        "account_name": messy_name_variant(base),
        "industry": random.choice(INDUSTRIES),  # sometimes re-entered inconsistently
        "country": fake.country(),
        "duns_number": "",  # duplicates usually missing DUNS
        "created_date": (TODAY - timedelta(days=random.randint(5, 730))).date(),
        "owner_rep_id": random.choice(reps_df.rep_id),
        "account_source": random.choice(["Inbound", "Outbound", "Partner", "Event", ""]),
    })
    acct_counter += 1

accounts_df = pd.DataFrame(accounts)
accounts_df.to_csv(f"{OUT}/accounts.csv", index=False)

# -------------------------------------------------------------- opportunities
STAGE_VARIANTS = {
    "Prospecting":   ["Prospecting", "prospecting", "PROSPECTING", "Prospect"],
    "Qualification": ["Qualification", "Qualifying", "qualification"],
    "Proposal":      ["Proposal", "Proposal Sent", "proposal"],
    "Negotiation":   ["Negotiation", "Negotiating", "negotiation"],
    "Closed Won":    ["Closed Won", "closed-won", "Won", "CLOSED WON"],
    "Closed Lost":   ["Closed Lost", "closed-lost", "Lost", "CLOSED LOST"],
}
PRODUCTS = ["Platform License", "Professional Services", "Support Add-on", "Data Module"]
LEAD_SOURCES = ["Outreach Sequence", "ZoomInfo List", "LinkedIn Sales Nav", "Inbound Web", "Referral", ""]

opps = []
for i in range(1, 901):
    acct = accounts_df.sample(1).iloc[0]
    rep = reps_df.sample(1).iloc[0]
    created_dt = TODAY - timedelta(days=random.randint(1, 545))
    created = created_dt.date()

    canonical_stage = random.choices(
        list(STAGE_VARIANTS.keys()),
        weights=[18, 20, 18, 12, 20, 12], k=1
    )[0]
    stage_raw = random.choice(STAGE_VARIANTS[canonical_stage])
    is_closed = canonical_stage in ("Closed Won", "Closed Lost")

    if is_closed:
        close_date = created_dt + timedelta(days=random.randint(10, 180))
        if close_date > TODAY:
            close_date = TODAY - timedelta(days=random.randint(1, 5))
        last_activity = close_date - timedelta(days=random.randint(0, 5))
    else:
        close_date = None
        # deliberately make a chunk of "open" opportunities stale (no recent activity)
        if random.random() < 0.35:
            last_activity = created_dt + timedelta(days=random.randint(1, 20))
        else:
            last_activity = TODAY - timedelta(days=random.randint(0, 25))

    amount = round(np.random.lognormal(mean=9.4, sigma=0.8), -2)
    if random.random() < 0.04:
        amount = None  # a few missing amounts

    opps.append({
        "opp_id": f"O{i:05d}",
        "account_id": acct.account_id,
        "opp_name": f"{acct.account_name.strip()} - {random.choice(PRODUCTS)}",
        "stage_raw": stage_raw,
        "amount": amount,
        "product": random.choice(PRODUCTS),
        "lead_source": random.choice(LEAD_SOURCES),
        "created_date": created,
        "close_date": close_date.date() if close_date else "",
        "last_activity_date": last_activity.date(),
        "rep_id": rep.rep_id,
    })

opps_df = pd.DataFrame(opps)
opps_df.to_csv(f"{OUT}/opportunities.csv", index=False)

print(f"accounts: {len(accounts_df)} rows ({len(duplicate_pool)} duplicated companies)")
print(f"reps: {len(reps_df)} rows")
print(f"opportunities: {len(opps_df)} rows")
