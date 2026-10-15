#!/usr/bin/env python3
"""
Generates assets/trophies.svg and assets/activity.svg for the profile README.

No third-party services, no extra dependencies (stdlib only).

Usage:
    GH_TOKEN=xxx python scripts/generate_profile_svgs.py     # real data
    python scripts/generate_profile_svgs.py --demo            # placeholder data
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = os.environ.get("PROFILE_LOGIN", "Rudra-Patel-CS")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path(os.environ.get("OUT_DIR", "assets"))
DEMO = "--demo" in sys.argv

# Palette (matches the README theme)
BG, BORDER, AMBER, GREEN = "#0B0F14", "#1F2A36", "#FFB020", "#3DD68C"
TEXT, MUTED, PANEL = "#C8D4E0", "#6B7C8F", "#131A22"
FONT = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){
      totalCount
      nodes{stargazerCount}
    }
    pullRequests{totalCount}
    issues{totalCount}
    contributionsCollection{
      totalCommitContributions
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
  }
}
"""


def fetch():
    if DEMO:
        today = dt.date.today()
        sample = [0, 2, 1, 4, 0, 3, 5, 2, 6, 1, 0, 2, 7, 3, 4, 1, 0, 5, 8, 2,
                  3, 6, 1, 4, 2, 0, 5, 3, 7, 4]
        days = [((today - dt.timedelta(days=29 - i)).isoformat(), c)
                for i, c in enumerate(sample)]
        stats = {"Stars": 3, "Commits": 120, "Followers": 8,
                 "Repos": 9, "PRs": 4, "Issues": 1}
        return stats, days

    if not TOKEN:
        raise SystemExit("Set GH_TOKEN (or GITHUB_TOKEN), or run with --demo.")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-svg-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(json.dumps(payload["errors"], indent=2))
    u = payload["data"]["user"]
    cc = u["contributionsCollection"]
    stats = {
        "Stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "Commits": cc["totalCommitContributions"],
        "Followers": u["followers"]["totalCount"],
        "Repos": u["repositories"]["totalCount"],
        "PRs": u["pullRequests"]["totalCount"],
        "Issues": u["issues"]["totalCount"],
    }
    days = [(d["date"], d["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    days = [d for d in days if d[0] <= dt.date.today().isoformat()]
    return stats, days


# ───────────────────────── Trophies ─────────────────────────
THRESH = {
    "Stars":     [1, 5, 20, 50, 150],
    "Commits":   [10, 50, 150, 400, 1000],
    "Followers": [1, 5, 15, 40, 100],
    "Repos":     [1, 5, 10, 25, 50],
    "PRs":       [1, 5, 15, 40, 100],
    "Issues":    [1, 3, 10, 25, 60],
}
RANKS = ["–", "C", "B", "A", "S", "SS"]
TIER_COLORS = ["#3A4756", "#CD7F32", "#AEB9C6", AMBER, GREEN, "#5CD6FF"]
SUBLABEL = {"Commits": "COMMITS · 1Y"}


def trophies_svg(stats):
    W, H, n = 764, 150, len(stats)
    cw = 116
    gap = (W - n * cw) / (n - 1)
    cards = []
    for i, (name, val) in enumerate(stats.items()):
        th = THRESH[name]
        rank = sum(1 for t in th if val >= t)
        color = TIER_COLORS[rank]
        prev = th[rank - 1] if rank > 0 else 0
        frac = 1.0 if rank == len(th) else (val - prev) / (th[rank] - prev)
        x = i * (cw + gap)
        label = SUBLABEL.get(name, name.upper())
        cards.append(f"""
  <g transform="translate({x:.1f},4)">
    <rect width="{cw}" height="142" rx="12" fill="{BG}" stroke="{BORDER}"/>
    <rect x="1" y="1" width="{cw-2}" height="3" rx="1.5" fill="{color}" opacity="0.9"/>
    <g transform="translate({cw/2},50)">
      <ellipse cx="0" cy="-4" rx="30" ry="26" fill="{color}" opacity="0.08">
        <animate attributeName="opacity" values="0.05;0.16;0.05" dur="3.2s" begin="{i*0.35:.2f}s" repeatCount="indefinite"/>
      </ellipse>
      <path d="M-13 -22 H13 V-10 C13 -1 7 5 0 5 C-7 5 -13 -1 -13 -10 Z" fill="{color}"/>
      <path d="M-13 -18 H-20 C-20 -8 -17 -4 -11 -3" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
      <path d="M13 -18 H20 C20 -8 17 -4 11 -3" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
      <rect x="-3" y="5" width="6" height="9" fill="{color}"/>
      <rect x="-11" y="14" width="22" height="5" rx="2" fill="{color}"/>
      <text x="0" y="-5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="{BG}">{RANKS[rank]}</text>
    </g>
    <text x="{cw/2}" y="92" text-anchor="middle" font-family="{FONT}" font-size="19" font-weight="700" fill="{TEXT}">{val:,}</text>
    <text x="{cw/2}" y="109" text-anchor="middle" font-family="{FONT}" font-size="9.5" letter-spacing="1.2" fill="{MUTED}">{escape(label)}</text>
    <rect x="18" y="123" width="{cw-36}" height="4" rx="2" fill="{PANEL}"/>
    <rect x="18" y="123" width="{(cw-36)*frac:.1f}" height="4" rx="2" fill="{color}"/>
  </g>""")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="GitHub trophies">'
            f'{"".join(cards)}\n</svg>\n')


# ───────────────────────── Activity ─────────────────────────
def activity_svg(days):
    days = days[-30:]
    W, H = 764, 270
    x0, x1, y0, y1 = 52, 736, 78, 218
    counts = [c for _, c in days]
    peak, total = max(counts + [0]), sum(counts)
    ymax = max(4, ((peak + 3) // 4) * 4)
    n = len(days)
    step = (x1 - x0) / max(n - 1, 1)
    pts = [(x0 + i * step, y1 - (c / ymax) * (y1 - y0)) for i, (_, c) in enumerate(days)]
    line = " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    grid = []
    for k in range(5):
        gy = y1 - k * (y1 - y0) / 4
        grid.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x1}" y2="{gy:.1f}" stroke="{BORDER}" stroke-dasharray="3 5"/>'
                    f'<text x="{x0-10}" y="{gy+4:.1f}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{MUTED}">{int(ymax*k/4)}</text>')
    xl = []
    for i in range(0, n, 6):
        d = dt.date.fromisoformat(days[i][0])
        xl.append(f'<text x="{pts[i][0]:.1f}" y="{y1+22}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{MUTED}">{d.strftime("%b %d")}</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{BG}" stroke="#FFD080" stroke-width="1.5"/>'
                   for (x, y), (_, c) in zip(pts, days) if c > 0)
    lx, ly = pts[-1]
    note = (f'<text x="{W/2}" y="{H-8}" text-anchor="middle" font-family="{FONT}" font-size="9" fill="{MUTED}">'
            f'placeholder data · refreshed by the profile-stats workflow</text>') if DEMO else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub commit activity, last 30 days">
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{AMBER}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{BG}" stroke="{BORDER}"/>
  <circle cx="26" cy="28" r="4" fill="#FF5F56"/><circle cx="42" cy="28" r="4" fill="#FFBD2E"/><circle cx="58" cy="28" r="4" fill="#27C93F"/>
  <text x="80" y="32" font-family="{FONT}" font-size="12" fill="{AMBER}" font-weight="700">commit_activity.log</text>
  <text x="{W-26}" y="32" text-anchor="end" font-family="{FONT}" font-size="11" fill="{MUTED}">last 30 days · total {total} · peak {peak}</text>
  <line x1="16" y1="48" x2="{W-16}" y2="48" stroke="{BORDER}"/>
  {"".join(grid)}
  <polygon points="{x0},{y1} {" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)} {x1},{y1}" fill="url(#fill)">
    <animate attributeName="opacity" from="0" to="1" dur="1.4s" fill="freeze"/>
  </polygon>
  <path d="M{line}" fill="none" stroke="{AMBER}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" pathLength="1">
    <animate attributeName="stroke-dasharray" values="0 1;1 0" dur="1.6s" fill="freeze"/>
  </path>
  {dots}
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{GREEN}">
    <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  {"".join(xl)}
  {note}
</svg>
"""


def main():
    stats, days = fetch()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "trophies.svg").write_text(trophies_svg(stats), encoding="utf-8")
    (OUT / "activity.svg").write_text(activity_svg(days), encoding="utf-8")
    print("wrote", OUT / "trophies.svg", "and", OUT / "activity.svg")


if __name__ == "__main__":
    main()
