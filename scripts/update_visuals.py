"""Render self-hosted profile visuals from public GitHub data."""

from __future__ import annotations

import json
import math
import os
from datetime import date
from pathlib import Path
import random
import subprocess
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get("PROFILE_USER", "Myosotis11037")
INK = "#eef1ff"
MUTED = "#8994bc"
LILAC = "#bdacff"
BLUE = "#7bd9f5"


def github_data() -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        token = subprocess.check_output(
            ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    query = """
    query($login: String!, $after: String) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                     privacy: PUBLIC) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount isFork }
        }
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    after = None
    stars = 0
    while True:
        payload = json.dumps({"query": query, "variables": {"login": USER, "after": after}})
        request = Request(
            "https://api.github.com/graphql",
            data=payload.encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                     "User-Agent": "Myosotis11037-profile-visuals"},
        )
        with urlopen(request, timeout=45) as response:
            result = json.load(response)
        if result.get("errors"):
            raise RuntimeError(json.dumps(result["errors"]))
        user = result["data"]["user"]
        if not user:
            raise RuntimeError("Profile user not found")
        repos = user["repositories"]
        stars += sum(repo["stargazerCount"] for repo in repos["nodes"] if not repo["isFork"])
        if not repos["pageInfo"]["hasNextPage"]:
            return {"followers": user["followers"]["totalCount"],
                    "repositories": repos["totalCount"], "stars": stars,
                    "calendar": user["contributionsCollection"]["contributionCalendar"]}
        after = repos["pageInfo"]["endCursor"]


def svg(height: int, body: str, extra_defs: str = "", styles: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" fill="none">
<defs>
  <linearGradient id="panel" x1="0" y1="0" x2="960" y2="{height}" gradientUnits="userSpaceOnUse">
    <stop stop-color="#11182e"/><stop offset=".5" stop-color="#14172d"/><stop offset="1" stop-color="#0d1425"/>
  </linearGradient>
  <linearGradient id="signal" x1="0" y1="0" x2="960" y2="0" gradientUnits="userSpaceOnUse"><stop stop-color="#7bd9f5"/><stop offset=".5" stop-color="#bdacff"/><stop offset="1" stop-color="#ebbbeb"/></linearGradient>
  <radialGradient id="halo"><stop stop-color="#8d79eb" stop-opacity=".32"/><stop offset="1" stop-color="#8d79eb" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>
  {extra_defs}
</defs>
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
  .breathe {{ animation: breathe 5s ease-in-out infinite; }}
  @keyframes breathe {{ 0%,100% {{opacity:.45}} 50% {{opacity:1}} }}
  {styles}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
{body}
</svg>
'''


def panel(height: int) -> str:
    return f'<rect x=".5" y=".5" width="959" height="{height-1}" rx="22" fill="url(#panel)" stroke="#303653"/>'


def header() -> str:
    rng = random.Random(11037)
    parts = [panel(300), '<ellipse cx="480" cy="135" rx="310" ry="205" fill="url(#halo)"/>']
    # Quiet astronomical grid, with no labels or invented telemetry.
    for x in range(40, 960, 40):
        parts.append(f'<path d="M{x} 24V276" stroke="#b2bfff" opacity=".025"/>')
    for y in range(30, 300, 30):
        parts.append(f'<path d="M24 {y}H936" stroke="#b2bfff" opacity=".025"/>')
    for i in range(65):
        x, y = rng.randint(30, 930), rng.randint(24, 265)
        radius = rng.choice([.7, .9, 1.2, 1.6])
        parts.append(f'<circle class="breathe" cx="{x}" cy="{y}" r="{radius}" fill="{BLUE if i % 3 else LILAC}" style="animation-delay:-{i % 8}s"/>')
    for x, y in [(125, 78), (804, 56), (845, 185), (220, 180)]:
        parts.append(f'<path d="M{x-5} {y}h10m-5-5v10" stroke="#c7d6ff" opacity=".65"/>')
    parts.append('<path d="M89 156L149 110L214 126L265 83M714 199L762 150L822 163L887 124" stroke="#8c9fcf" stroke-opacity=".23"/>')
    for x, y in [(89,156),(149,110),(214,126),(265,83),(714,199),(762,150),(822,163),(887,124)]:
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.3" fill="#a6b9e8"/>')
    # Edge-on orbits frame a five-petal forget-me-not, with a crescent core.
    parts.append('<ellipse cx="480" cy="135" rx="184" ry="59" transform="rotate(-16 480 135)" stroke="url(#signal)" stroke-opacity=".38"/>')
    parts.append('<ellipse cx="480" cy="135" rx="150" ry="83" transform="rotate(25 480 135)" stroke="#99b5ed" stroke-opacity=".18"/>')
    parts.append('<circle cx="480" cy="135" r="92" stroke="#aaa0e9" stroke-opacity=".15" stroke-dasharray="2 9"/>')
    parts.append('<g class="orbit"><circle cx="656.8" cy="84.3" r="4" fill="#a7eaff"/><circle cx="656.8" cy="84.3" r="8" fill="#7bd9f5" opacity=".16"/></g>')
    parts.append('<circle cx="480" cy="135" r="67" fill="#10192f" fill-opacity=".8" stroke="#8ca0d1" stroke-opacity=".25"/>')
    petals = []
    for angle in range(0, 360, 72):
        petals.append(f'<path d="M480 132C451 119 449 89 467 83C489 74 506 104 480 132Z" transform="rotate({angle} 480 135)"/>')
    flower = ''.join(petals)
    parts.append(f'<g fill="url(#signal)" opacity=".22" filter="url(#glow)">{flower}</g>')
    parts.append(f'<g fill="url(#petal)" stroke="url(#signal)" stroke-width="1.3">{flower}</g>')
    parts.append('<circle cx="480" cy="135" r="12" fill="#151c33" stroke="#ccbeff"/>')
    parts.append('<path d="M484 126a9 9 0 1 0 4 13a8 8 0 0 1-4-13Z" fill="#d6d0ff"/>')
    # A restrained spectrum feels musical; this is decoration, not activity data.
    for i in range(87):
        x = 48 + i * 10
        envelope = math.exp(-((i-43)/25)**2)
        amplitude = 3 + envelope * (8 + 20 * abs(math.sin(i * .68)))
        parts.append(f'<path class="spectrum" d="M{x} {256-amplitude:.1f}V{256+amplitude:.1f}" stroke="url(#signal)" stroke-width="2.6" stroke-linecap="round" opacity="{.25+.5*envelope:.2f}" style="animation-delay:-{i*.13:.2f}s"/>')
    parts.append('<path d="M30 256H930" stroke="url(#signal)" stroke-opacity=".1"/>')
    return svg(300, ''.join(parts), '<linearGradient id="petal" x1="450" y1="80" x2="505" y2="165" gradientUnits="userSpaceOnUse"><stop stop-color="#7bd9f5" stop-opacity=".35"/><stop offset="1" stop-color="#b39af7" stop-opacity=".08"/></linearGradient>', '''
      .orbit { transform-origin:480px 135px; animation:orbit 24s linear infinite; }
      @keyframes orbit { to { transform:rotate(360deg); } }
      .spectrum { transform-box:fill-box; transform-origin:center; animation:spectrum 3s ease-in-out infinite; }
      @keyframes spectrum { 0%,100% {transform:scaleY(.65)} 50% {transform:scaleY(1)} }
    ''')


ICONS = {
    "followers": '<circle cx="10" cy="8" r="3"/><path d="M4 21v-3a6 6 0 0 1 12 0v3M17 5a3 3 0 0 1 0 6m3 10v-3a6 6 0 0 0-3-5"/>',
    "repositories": '<path d="M5 3h14v18H6a3 3 0 0 1 0-6h13M5 3v12m4-8h6m-6 3h4"/>',
    "stars": '<path d="m12 2 3 6.3 7 .9-5 4.9 1.2 6.9-6.2-3.3L5.8 21 7 14.1 2 9.2l7-.9Z"/>',
    "contributions": '<path d="M2 13h4l3-9 5 17 3-8h5"/>',
}


def icon(name: str, x: float, y: float, scale: float = 1) -> str:
    return f'<g transform="translate({x} {y}) scale({scale})" stroke="url(#signal)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>'


def metrics(data: dict) -> str:
    parts = []
    values = [("followers", data["followers"], "关注者"),
              ("repositories", data["repositories"], "公开个人仓库"),
              ("stars", data["stars"], "个人原创公开仓库获星"),
              ("contributions", data["calendar"]["totalContributions"], "近一年贡献")]
    for i, (name, value, title) in enumerate(values):
        x = i * 244
        parts.append(f'<g><title>{title}</title><rect x="{x+.5}" y=".5" width="227" height="143" rx="18" fill="url(#panel)" stroke="#303653"/>')
        parts.append(f'<circle cx="{x+34}" cy="34" r="23" fill="#bdacff" opacity=".04"/>')
        parts.append(icon(name, x+22, 22))
        parts.append(f'<text x="{x+20}" y="110" fill="{INK}" font-size="38" font-weight="600" letter-spacing="-1">{value:,}</text>')
        parts.append(f'<path d="M{x+20} 128h32" stroke="url(#signal)" stroke-width="2" stroke-linecap="round"/></g>')
    return svg(144, ''.join(parts))


def activity(calendar: dict) -> str:
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    max_count = max((d["contributionCount"] for d in days), default=0)
    colors = ["#1c2540", "#3b426f", "#655b9f", "#9b8bdd", "#c6b7ff"]
    parts = [panel(255), icon("contributions", 28, 23)]
    start, end = days[0]["date"].replace("-", "."), days[-1]["date"].replace("-", ".")
    parts.append(f'<text x="69" y="41" fill="{MUTED}" font-size="13">{start} — {end}</text>')
    # Fit 53 or 54 weeks without dropping any days.
    pitch = min(17, 890 / len(weeks))
    size = pitch - 4
    x_start = (960 - (len(weeks) * pitch - 4)) / 2
    for col, week in enumerate(weeks):
        for day in week["contributionDays"]:
            row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            count = day["contributionCount"]
            level = 0 if count == 0 else min(4, 1 + int(3 * math.log1p(count) / math.log1p(max_count)))
            x, y = x_start + col * pitch, 68 + row * pitch
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" rx="3" fill="{colors[level]}"><title>{day["date"]}: {count}</title></rect>')
    # Actual weekly totals, normalized only for the sparkline height.
    counts = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    maximum = max(counts, default=1) or 1
    coordinates = [(x_start + i*pitch + size/2, 224 - value/maximum*25) for i, value in enumerate(counts)]
    points = ' '.join(f'{x:.2f},{y:.2f}' for x, y in coordinates)
    fill_points = f'{coordinates[0][0]:.2f},229 {points} {coordinates[-1][0]:.2f},229'
    parts.append(f'<polygon points="{fill_points}" fill="url(#signal)" opacity=".07"/>')
    parts.append(f'<polyline points="{points}" stroke="url(#signal)" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"/>')
    return svg(255, ''.join(parts))


def main() -> None:
    data = github_data()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    outputs = {"night-signal.svg": header(), "metrics.svg": metrics(data),
               "activity.svg": activity(data["calendar"])}
    # Fetch and render everything before changing any committed assets.
    for name, content in outputs.items():
        normalized = '\n'.join(line.rstrip() for line in content.splitlines()) + '\n'
        (assets / name).write_text(normalized, encoding="utf-8")
    print(json.dumps({key: data[key] for key in ("followers", "repositories", "stars")} |
                     {"contributions": data["calendar"]["totalContributions"]}))


if __name__ == "__main__":
    main()
