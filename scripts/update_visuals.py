"""Render a project showcase and public development activity for the profile."""

from __future__ import annotations

import base64
from datetime import date
from html import escape
import json
import math
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get("PROFILE_USER", "Myosotis11037")
PROJECT = "karaoke-studio/karaoke-studio"
INK = "#f1efff"
MUTED = "#9ca7c4"
LILAC = "#c3b0ff"
BLUE = "#83e2e4"


def fetch(url: str, token: str = "", payload: dict | None = None) -> bytes:
    headers = {"User-Agent": "Myosotis11037-profile-visuals"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, headers=headers,
                      data=json.dumps(payload).encode() if payload is not None else None)
    with urlopen(request, timeout=45) as response:
        return response.read()


def github_data() -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        token = subprocess.check_output(
            ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
          commitContributionsByRepository(maxRepositories: 100) {
            repository { nameWithOwner }
            contributions { totalCount }
          }
        }
      }
      repository(owner: "karaoke-studio", name: "karaoke-studio") {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          totalSize
          edges { size node { name } }
        }
      }
    }
    """
    result = json.loads(fetch("https://api.github.com/graphql", token,
                              {"query": query, "variables": {"login": USER}}))
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))
    user = result["data"]["user"]
    project = result["data"]["repository"]
    if not user or not project:
        raise RuntimeError("Public profile or featured project not found")
    release = json.loads(fetch(f"https://api.github.com/repos/{PROJECT}/releases/latest", token))
    screenshot = fetch(f"https://raw.githubusercontent.com/{PROJECT}/main/assets/shot-subtitle.png")
    return {"activity": user["contributionsCollection"], "languages": project["languages"],
            "version": release["tag_name"], "screenshot": base64.b64encode(screenshot).decode()}


def text(x: float, y: float, value: object, size: float = 14,
         color: str = INK, weight: int = 400, extra: str = "") -> str:
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" {extra}>{escape(str(value))}</text>')


def svg(height: int, body: str, defs: str = "", styles: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" fill="none">
<defs>
  <linearGradient id="panel" x1="0" y1="0" x2="960" y2="{height}" gradientUnits="userSpaceOnUse">
    <stop stop-color="#131a30"/><stop offset=".6" stop-color="#17182e"/><stop offset="1" stop-color="#101927"/>
  </linearGradient>
  <linearGradient id="signal" x1="0" y1="0" x2="960" y2="0" gradientUnits="userSpaceOnUse">
    <stop stop-color="#83e2e4"/><stop offset=".55" stop-color="#c3b0ff"/><stop offset="1" stop-color="#f0a7c8"/>
  </linearGradient>
  <radialGradient id="halo"><stop stop-color="#9273db" stop-opacity=".3"/><stop offset="1" stop-color="#9273db" stop-opacity="0"/></radialGradient>
  {defs}
</defs>
<style>
  text {{ font-family: "Segoe UI", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; }}
  .mono {{ font-family: Consolas, "SFMono-Regular", monospace; }}
  {styles}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
</style>
{body}
</svg>
'''


def panel(height: int) -> str:
    return f'<rect x=".5" y=".5" width="959" height="{height-1}" rx="24" fill="url(#panel)" stroke="#343650"/>'


def project_showcase(data: dict) -> str:
    parts = [panel(470), '<ellipse cx="722" cy="230" rx="410" ry="310" fill="url(#halo)"/>']
    parts.append('<path d="M30 60H930" stroke="#a995e8" stroke-opacity=".15"/>')
    parts.append('<circle class="pulse" cx="37" cy="33" r="3" fill="#83e2e4"/>')
    parts.append(text(51, 38, "Co-maintained project", 12, MUTED))
    parts.append(text(925, 38, "01 / PROJECT", 11, MUTED, extra='text-anchor="end"'))
    parts.append(text(34, 125, "Lin-K Lyrics", 44, INK, 650, 'letter-spacing="-1.5"'))
    parts.append(text(36, 164, "凛K", 22, LILAC, 600))
    parts.append(text(36, 211, "卡拉OK一站式工作台", 18, INK, 500))
    parts.append(text(36, 240, "从素材下载到 Hi-Res 成品", 14, MUTED))
    for x, label, width in [(36, "Python", 72), (118, "PyQt6", 69), (197, "C++", 57)]:
        parts.append(f'<rect x="{x}" y="267" width="{width}" height="28" rx="7" fill="#bda7f3" fill-opacity=".07" stroke="#afa0d5" stroke-opacity=".16"/>')
        parts.append(text(x+width/2, 286, label, 12, LILAC, extra='text-anchor="middle"'))
    parts.append('<rect x="36" y="324" width="150" height="40" rx="10" fill="#c3b0ff"/>')
    parts.append(text(57, 350, "View project", 14, "#171629", 650))
    parts.append(text(158, 350, "↗", 19, "#171629", 600))
    parts.append(text(36, 399, data["version"], 12, MUTED, extra='class="mono"'))
    for i in range(28):
        x = 148 + i*5.7
        amp = 3 + 10*abs(math.sin(i*.73))*math.exp(-((i-14)/11)**2)
        parts.append(f'<path class="spectrum" d="M{x:.1f} {395-amp:.1f}V{395+amp:.1f}" stroke="url(#signal)" stroke-width="2" stroke-linecap="round" style="animation-delay:-{i*.14:.2f}s"/>')
    parts.append('<rect x="354" y="80" width="572" height="366" rx="14" fill="#080d18" stroke="#777295" stroke-opacity=".45"/>')
    parts.append('<circle cx="370" cy="94" r="2.3" fill="#f0a7c8"/><circle cx="380" cy="94" r="2.3" fill="#c3b0ff"/><circle cx="390" cy="94" r="2.3" fill="#83e2e4"/>')
    parts.append(text(910, 98, "字幕视频生成", 10, MUTED, extra='text-anchor="end"'))
    parts.append(f'<image href="data:image/png;base64,{data["screenshot"]}" x="362" y="108" width="556" height="330" preserveAspectRatio="xMidYMid meet"/>')
    return svg(470, ''.join(parts), styles='''
      .pulse { animation:pulse 4s ease-in-out infinite; }
      @keyframes pulse { 50% { opacity:.3; } }
      .spectrum { transform-box:fill-box; transform-origin:center; animation:spectrum 3s ease-in-out infinite; }
      @keyframes spectrum { 0%,100% {transform:scaleY(.55)} 50% {transform:scaleY(1)} }
    ''')


def development(data: dict) -> str:
    activity = data["activity"]
    weeks = activity["contributionCalendar"]["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    active_days = sum(day["contributionCount"] > 0 for day in days)
    commits = activity["totalCommitContributions"]
    project_commits = next((repo["contributions"]["totalCount"] for repo in activity["commitContributionsByRepository"]
                            if repo["repository"]["nameWithOwner"] == PROJECT), 0)
    start, end = days[0]["date"].replace("-", "."), days[-1]["date"].replace("-", ".")
    parts = [panel(440)]
    parts.append(text(32, 38, "Development Activity", 18, INK, 600))
    parts.append(text(927, 36, f"{start} — {end}", 11, MUTED,
                      extra='text-anchor="end" class="mono"'))
    parts.append(text(32, 118, f"{commits:,}", 51, INK, 600, 'class="mono" letter-spacing="-2"'))
    parts.append(text(34, 148, "Public commits · past year", 12, MUTED))
    parts.append('<path d="M34 170H210" stroke="#353c58"/>')
    parts.append(text(34, 200, "Pull Requests", 12, MUTED))
    parts.append(text(210, 200, activity["totalPullRequestContributions"], 19, BLUE, 600, 'text-anchor="end" class="mono"'))
    parts.append(text(34, 232, "Active Days", 12, MUTED))
    parts.append(text(210, 232, active_days, 19, LILAC, 600, 'text-anchor="end" class="mono"'))
    parts.append('<path d="M246 76V248" stroke="#353c58"/>')
    parts.append(text(277, 88, "Contribution Rhythm", 13, INK, 500))
    parts.append(text(925, 88, "Weekly contributions · past 26 weeks", 11, MUTED, extra='text-anchor="end"'))
    recent = weeks[-26:]
    counts = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in recent]
    maximum = max(counts, default=0) or 1
    peak = max(10, math.ceil(maximum/50)*50)
    for fraction in (0, .5, 1):
        y = 228 - fraction*111
        parts.append(f'<path d="M278 {y}H904" stroke="#8794bc" stroke-opacity=".12" stroke-dasharray="3 6"/>')
        parts.append(text(925, y+4, int(peak*fraction), 10, MUTED, extra='text-anchor="end" class="mono"'))
    for i, (week, count) in enumerate(zip(recent, counts)):
        x = 279+i*24
        height = count/peak*111
        parts.append(f'<rect x="{x}" y="{228-height:.2f}" width="13" height="{max(height,1):.2f}" rx="3" fill="url(#signal)" opacity="{.9 if count else .12}"><title>{week["contributionDays"][0]["date"]}: {count}</title></rect>')
    for index, anchor, x in [(0, "start", 278), (13, "middle", 597), (25, "end", 902)]:
        stamp = date.fromisoformat(recent[index]["contributionDays"][0]["date"])
        parts.append(text(x, 248, stamp.strftime("%m.%d"), 10, MUTED, extra=f'text-anchor="{anchor}" class="mono"'))
    share = project_commits/commits if commits else 0
    parts.append('<rect x="32" y="275" width="896" height="36" rx="8" fill="#c3b0ff" fill-opacity=".055"/>')
    parts.append(text(46, 298, "Lin-K Lyrics", 12, LILAC, 600))
    parts.append(text(172, 298, f"{project_commits:,} commits", 12, INK, 500))
    parts.append(text(912, 298, f"{share:.1%} of public commits this year", 11, MUTED, extra='text-anchor="end"'))
    parts.append('<path d="M32 332H928" stroke="#353c58"/>')
    parts.append(text(32, 359, "Lin-K Languages", 13, INK, 500))
    parts.append(text(927, 359, "By code size · GitHub Linguist", 10, MUTED, extra='text-anchor="end"'))
    languages = data["languages"]
    total = languages["totalSize"]
    if total:
        primary = languages["edges"][:2]
        groups = [(edge["node"]["name"], edge["size"]) for edge in primary]
        remainder = total-sum(size for _, size in groups)
        if remainder:
            groups.append(("Other", remainder))
        colors = [LILAC, BLUE, "#f0a7c8"]
        x = 32.0
        for index, (name, size) in enumerate(groups):
            width = size/total*896
            parts.append(f'<rect x="{x:.3f}" y="375" width="{width:.3f}" height="10" fill="{colors[index]}"/>')
            x += width
            label_x = 32+index*307
            parts.append(f'<circle cx="{label_x+4}" cy="409" r="3" fill="{colors[index]}"/>')
            parts.append(text(label_x+16, 413, f"{name}  {size/total:.1%}", 12, MUTED))
    else:
        parts.append(text(32, 403, "No language data available", 12, MUTED))
    return svg(440, ''.join(parts))


def main() -> None:
    data = github_data()
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    outputs = {"project.svg": project_showcase(data), "development.svg": development(data)}
    for name, content in outputs.items():
        normalized = '\n'.join(line.rstrip() for line in content.splitlines()) + '\n'
        (assets / name).write_text(normalized, encoding="utf-8")
    print(json.dumps({"commits": data["activity"]["totalCommitContributions"],
                      "pull_requests": data["activity"]["totalPullRequestContributions"],
                      "version": data["version"]}))


if __name__ == "__main__":
    main()
