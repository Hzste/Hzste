"""Builds the profile stat cards (generated/stats.svg, generated/langs.svg)
from live GitHub data. Runs inside GitHub Actions with the default token."""
import json
import os
import urllib.request

USER = "Hzste"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG = "#09131B"
BORDER = "#0c1a25"
TITLE = "#FD0000"
ACCENT = "#16AEE3"
TEXT = "#ffffff"
MUTED = "#8b949e"

LANG_COLOURS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#563d7c", "PHP": "#4F5D95", "C#": "#178600", "Swift": "#F05138",
    "Shell": "#89e051", "TypeScript": "#3178c6", "Java": "#b07219",
    "C++": "#f34b7d", "C": "#555555", "Go": "#00ADD8", "Kotlin": "#A97BFF",
    "Jupyter Notebook": "#DA5B0B", "Vue": "#41b883", "Dockerfile": "#384d54",
    "Makefile": "#427819", "Objective-C": "#438eff", "Ruby": "#701516",
}


def get(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_all_repos():
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def search_count(query):
    try:
        return int(get(f"https://api.github.com/search/{query}").get("total_count", 0))
    except Exception:
        return 0


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;")


def card(width, height, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" fill="none" role="img">'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<text x="24" y="34" font-family="\'Segoe UI\', Ubuntu, Helvetica, Arial, sans-serif" '
        f'font-size="17" font-weight="700" fill="{TITLE}">{esc(title)}</text>'
        + body + "</svg>"
    )


def stats_svg(rows):
    body = ""
    y = 66
    for label, value in rows:
        body += (
            f'<circle cx="30" cy="{y - 5}" r="3" fill="{ACCENT}"/>'
            f'<text x="44" y="{y}" font-family="\'Segoe UI\', Ubuntu, Helvetica, Arial, sans-serif" '
            f'font-size="14" font-weight="600" fill="{TEXT}">{esc(label)}</text>'
            f'<text x="330" y="{y}" font-family="\'Segoe UI\', Ubuntu, Helvetica, Arial, sans-serif" '
            f'font-size="14" font-weight="700" fill="{ACCENT}">{esc(value)}</text>'
        )
        y += 27
    return card(400, y - 27 + 24, "Huseyin's GitHub Stats", body)


def langs_svg(langs):
    total = sum(b for _, b in langs) or 1
    body = ""
    # stacked bar
    x = 24.0
    bar_w = 352.0
    for name, b in langs:
        w = bar_w * b / total
        colour = LANG_COLOURS.get(name, MUTED)
        body += f'<rect x="{x:.1f}" y="52" width="{max(w, 2):.1f}" height="10" rx="2" fill="{colour}"/>'
        x += w
    # legend, two columns
    y = 88
    for i, (name, b) in enumerate(langs):
        col = i % 2
        row = i // 2
        lx = 24 + col * 180
        ly = y + row * 24
        colour = LANG_COLOURS.get(name, MUTED)
        pct = 100.0 * b / total
        body += (
            f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{colour}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="\'Segoe UI\', Ubuntu, Helvetica, Arial, sans-serif" '
            f'font-size="13" fill="{TEXT}">{esc(name)} '
            f'<tspan fill="{MUTED}">{pct:.1f}%</tspan></text>'
        )
    rows = (len(langs) + 1) // 2
    return card(400, y + rows * 24 - 24 + 16, "Most Used Languages", body)


def main():
    user = get(f"https://api.github.com/users/{USER}")
    repos = fetch_all_repos()
    own = [r for r in repos if not r.get("fork")]

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    commits = search_count(f"commits?q=author:{USER}")
    prs = search_count(f"issues?q=author:{USER}+type:pr")
    issues = search_count(f"issues?q=author:{USER}+type:issue")

    lang_bytes = {}
    for r in own:
        try:
            for lang, b in get(r["languages_url"]).items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + b
        except Exception:
            continue
    top = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:6]

    rows = [
        ("Total Stars Earned", stars),
        ("Total Commits", commits),
        ("Pull Requests", prs),
        ("Issues", issues),
        ("Followers", user.get("followers", 0)),
        ("Public Repositories", user.get("public_repos", 0)),
    ]

    os.makedirs("generated", exist_ok=True)
    with open("generated/stats.svg", "w") as f:
        f.write(stats_svg(rows))
    with open("generated/langs.svg", "w") as f:
        f.write(langs_svg(top) if top else card(400, 60, "Most Used Languages", ""))
    print("cards written:", rows, top)


if __name__ == "__main__":
    main()
