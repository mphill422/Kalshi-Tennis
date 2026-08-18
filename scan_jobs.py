#!/usr/bin/env python3
"""
Medical Sales & Client Roles Scanner - Mike Hill
Two tracks, IC only:
  A) Sales: account manager, account executive (incl. senior),
     pharmaceutical sales rep/executive, inside sales
  B) Client/relationship: customer success, client success,
     solutions consultant, provider relations, onboarding manager
No management, no strategic titles, no BDR/SDR, no implementation roles.
Remote, hybrid, field-based, and Florida-territory positions.
Writes JOBS.md daily via GitHub Action.
"""
import json, urllib.request, urllib.error
from datetime import date

# ---- filters -------------------------------------------------------------
TITLE_KEYWORDS = [
    # Track A - IC sales
    "account manager",
    "account executive",
    "pharmaceutical sales",
    "inside sales",
    "sales representative",
    "sales specialist",
    "clinical specialist",
    # Track B - client / relationship (no cold calling)
    "customer success",
    "client success",
    "client manager",
    "client partner",
    "relationship manager",
    "solutions consultant",
    "solution consultant",
    "clinical solutions",
    "provider relations",
    "provider engagement",
    "onboarding manager",
]
TITLE_EXCLUDE = [
    "director", "vice president", "vp", "avp", "gvp", "chief", "head of",
    "sales manager", "training manager", "regional manager", "area manager",
    "national sales", "strategic", "sr manager", "senior manager",
    "manager of", "president", "principal", "supervisor", "lead,",
    "business development representative", "bdr", "sdr",
    "sales development", "implementation",
    "engineer", "developer", "scientist", "intern", "software", "designer",
    "recruiter", "counsel", "accountant", "nurse", "administrator",
    "analyst",
]
REMOTE_HINTS = ["remote", "hybrid", "field", "united states", "us -", "- us",
                "usa", "southeast", "florida", "orlando", "tampa", ", fl",
                "east", "national"]

def want(title, location):
    t, loc = title.lower(), (location or "").lower()
    if not any(k in t for k in TITLE_KEYWORDS): return False
    if any(k in t for k in TITLE_EXCLUDE): return False
    if REMOTE_ONLY and loc and not any(h in loc for h in REMOTE_HINTS): return False
    return True

REMOTE_ONLY = True  # set False to see every location

# ---- fetchers ------------------------------------------------------------
def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def greenhouse(token):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs")
    for j in data.get("jobs", []):
        yield j.get("title",""), (j.get("location") or {}).get("name",""), j.get("absolute_url","")

def lever(token):
    data = get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    for j in data:
        yield j.get("text",""), (j.get("categories") or {}).get("location",""), j.get("hostedUrl","")

# ---- main ----------------------------------------------------------------
def main():
    companies = []
    for line in open("companies.txt"):
        line = line.strip()
        if not line or line.startswith("#"): continue
        source, token, name = [p.strip() for p in line.split(",", 2)]
        companies.append((source, token, name))

    hits, dead = [], []
    for source, token, name in companies:
        try:
            fetch = greenhouse if source == "gh" else lever
            for title, loc, url in fetch(token):
                if want(title, loc):
                    hits.append((name, title, loc, url))
        except Exception:
            dead.append(f"{name} ({source}:{token})")

    hits.sort()
    with open("JOBS.md", "w") as f:
        f.write(f"# Medical Sales & Client Roles (IC) - {date.today()}\n\n")
        f.write(f"**{len(hits)} matching roles** across {len(companies)-len(dead)} live boards\n\n")
        last = None
        for name, title, loc, url in hits:
            if name != last:
                f.write(f"\n## {name}\n")
                last = name
            f.write(f"- [{title}]({url}) \u2014 {loc}\n")
        if dead:
            f.write(f"\n---\n*Boards not resolving (prune or fix token in companies.txt):* {', '.join(dead)}\n")
    print(f"{len(hits)} roles written to JOBS.md; {len(dead)} dead boards")

if __name__ == "__main__":
    main()
