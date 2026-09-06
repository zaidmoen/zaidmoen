"""Fetch public GitHub metrics and render repository-hosted profile cards.

Python 3.10+; standard library only. Errors abort before replacing output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import math
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COLORS = ['#65b5ff', '#ae97ff', '#43d8c3', '#ffcb75', '#f187b9', '#95adc7']


def api(path: str) -> object:
    headers = {'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'zaidmoen-profile-stats'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=30) as response:
        return json.load(response)


def search_count(endpoint: str, query: str) -> int:
    result = api(endpoint + '?' + urlencode({'q': query, 'per_page': 1}))
    if result.get('incomplete_results'):
        raise RuntimeError('Incomplete GitHub search: retaining the previous snapshot')
    return result['total_count']


def month_keys(now: datetime) -> list[str]:
    index = now.year * 12 + now.month - 1
    return [f'{i // 12:04d}-{i % 12 + 1:02d}' for i in range(index - 11, index + 1)]


def original_repos(user: str, repos: list[dict]) -> list[dict]:
    return [r for r in repos if not r['fork'] and not r['private']
            and r['owner']['login'].casefold() == user.casefold()]


def summarize(user: str, repos: list[dict], followers: int, public_commits: int,
              monthly_commits: list[dict], now: datetime) -> dict:
    original = original_repos(user, repos)
    languages = Counter(r['language'] for r in original if r.get('language'))
    return {
        'user': user, 'updated_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'scope': 'Public data only; repository metrics exclude forks.',
        'original_repositories': len(original),
        'stars': sum(r['stargazers_count'] for r in original),
        'followers': followers,
        'public_commits': public_commits,
        'commits_last_12_months': sum(item['count'] for item in monthly_commits),
        'languages': [{'name': name, 'repositories': count}
                      for name, count in sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))],
        'repositories_without_language': sum(not r.get('language') for r in original),
        'monthly_commits': monthly_commits,
        'sources': [f'https://api.github.com/users/{user}',
                    f'https://api.github.com/users/{user}/repos',
                    'https://api.github.com/search/commits',
                    f'https://api.github.com/repos/{user}/{{repo}}/commits'],
    }


def fetch_monthly_commits(user: str, original: list[dict], months: list[str]) -> list[dict]:
    """Count commits authored by `user` in their own original repositories, by month.

    Uses the per-repository commits endpoint (not /search/commits) so a single
    expired or missing token never affects more than the current repository,
    and empty repositories (409 Conflict) are simply skipped.
    """
    since = f'{months[0]}-01T00:00:00Z'
    window = set(months)
    histogram = Counter()
    for repo in original:
        page = 1
        while True:
            query = urlencode({'author': user, 'since': since, 'per_page': 100, 'page': page})
            try:
                batch = api(f'/repos/{user}/{repo["name"]}/commits?{query}')
            except HTTPError as error:
                if error.code == 409:
                    break  # Empty repository: no commits to count yet.
                raise
            if not batch:
                break
            for commit in batch:
                date = (commit.get('commit') or {}).get('author', {}).get('date')
                if date and date[:7] in window:
                    histogram[date[:7]] += 1
            if len(batch) < 100:
                break
            page += 1
    return [{'month': month, 'count': histogram[month]} for month in months]


def fetch_snapshot(user: str) -> dict:
    now = datetime.now(timezone.utc)
    profile = api(f'/users/{user}')
    repos = []
    page = 1
    while True:
        batch = api(f'/users/{user}/repos?per_page=100&type=owner&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    public_commits = search_count('/search/commits', f'author:{user}')
    months = month_keys(now)
    monthly = fetch_monthly_commits(user, original_repos(user, repos), months)
    return summarize(user, repos, profile['followers'], public_commits, monthly, now)


def txt(x, y, value, size=18, color='#ebf3ff', weight=400, extra=''):
    return (f'<text x="{x}" y="{y}" font-family="DejaVu Sans,Arial,sans-serif" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>'
            f'{escape(str(value))}</text>')


def panel(title, description, body, width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0" stop-color="#101e33"/><stop offset="1" stop-color="#060d19"/></linearGradient>
<linearGradient id="blue"><stop offset="0" stop-color="#2377f5"/><stop offset="1" stop-color="#72d9ff"/></linearGradient>
</defs><rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="#283f5e"/>
{body}</svg>'''


def overview(s):
    body = txt(34, 41, 'GITHUB / ENGINEERING SNAPSHOT', 13, '#82baff', 600, 'letter-spacing="2"')
    body += txt(1086, 41, 'PUBLIC DATA', 11, '#91aac9', extra='text-anchor="end"')
    body += '<path d="M34 63H1086" stroke="#233a58"/>'
    metrics = [('original_repositories', 'Original repositories'), ('stars', 'Stars received'),
               ('public_commits', 'Public commits'), ('commits_last_12_months', 'Commits · last 12 months')]
    for i, (key, label) in enumerate(metrics):
        x = 34 + i * 276
        color = '#72d9ff' if key in {'public_commits', 'commits_last_12_months'} else '#ebf3ff'
        body += txt(x, 131, f'{s[key]:,}', 48, color, 700)
        body += txt(x, 162, label, 14, '#9fb5d2')
        if i < 3:
            body += f'<path d="M{x+246} 90V170" stroke="#243952"/>'
    body += txt(34, 207, f"{s['followers']} followers  /  Public repositories and authored commit activity", 12, '#88a2c2')
    stamp = datetime.fromisoformat(s['updated_at'].replace('Z', '+00:00')).strftime('%d %b %Y · %H:%M UTC')
    body += txt(1086, 207, stamp, 11, '#88a2c2', extra='text-anchor="end"')
    return panel('GitHub engineering snapshot', s['scope'] + f" Updated {s['updated_at']}.", body, 1120, 235)


def language_card(s):
    body = txt(28, 40, 'Repository languages', 24, weight=600)
    body += txt(28, 68, 'Primary language per public original repository', 12, '#91aac9')
    langs = s['languages']
    display = langs[:5]
    if len(langs) > 5:
        display = display + [{'name': 'Other', 'repositories': sum(x['repositories'] for x in langs[5:])}]
    total = sum(x['repositories'] for x in langs)
    start = 28
    for i, entry in enumerate(display):
        width = 504 * entry['repositories'] / total if total else 0
        body += f'<rect x="{start:.2f}" y="94" width="{width:.2f}" height="13" fill="{COLORS[i]}"/>'
        start += width
    if not total:
        body += txt(28, 144, 'No language data available.', 15, '#a9bfdc')
    for i, entry in enumerate(display):
        y = 143 + i * 29
        pct = 100 * entry['repositories'] / total
        body += f'<circle cx="34" cy="{y-5}" r="4" fill="{COLORS[i]}"/>'
        body += txt(49, y, entry['name'], 14)
        body += txt(532, y, f"{entry['repositories']} repos · {pct:.1f}%", 13, '#a6bddb', extra='text-anchor="end"')
    body += txt(28, 345, f"{total} classified · {s['repositories_without_language']} without a detected language", 11, '#819abb')
    return panel('Repository language distribution', 'Repository counts, not lines of code or skill ratings.', body, 560, 373)


def activity_card(s):
    points = s['monthly_commits']
    body = txt(28, 40, 'Commit activity', 24, weight=600)
    body += txt(28, 68, 'Commits authored · trailing 12 calendar months', 12, '#91aac9')
    top = max(1, max((p['count'] for p in points), default=0))
    scale = max(2, math.ceil(top / 2) * 2)
    bottom, chart_height = 273, 153
    for count in [0, scale // 2, scale]:
        y = bottom - chart_height * count / scale
        body += f'<path d="M50 {y:.2f}H532" stroke="#213652" stroke-dasharray="3 5"/>'
        body += txt(37, y + 4, count, 11, '#829cbe', extra='text-anchor="end"')
    for i, point in enumerate(points):
        x = 60 + i * 39
        height = chart_height * point['count'] / scale
        body += f'<rect x="{x}" y="{bottom-height:.2f}" width="23" height="{height:.2f}" rx="4" fill="url(#blue)"><title>{escape(point["month"])}: {point["count"]} commits</title></rect>'
        if point['count']:
            body += txt(x+11.5, bottom-height-10, point['count'], 12, '#d2e9ff', extra='text-anchor="middle"')
        month = datetime.strptime(point['month'], '%Y-%m').strftime('%b')
        body += txt(x+11.5, 297, month, 10, '#91aac9', extra='text-anchor="middle"')
    body += txt(28, 345, f"{points[0]['month']} – {points[-1]['month']} · Current month is partial", 11, '#819abb')
    return panel('Monthly commit activity', 'Commits authored by the profile owner across original public repositories; the current month is partial. This is not a full contributions graph — private-repository and forked-repository commits are excluded.', body, 560, 373)



def overview_mobile(s):
    body = txt(28, 36, 'GITHUB / ENGINEERING SNAPSHOT', 12, '#82baff', 600)
    metrics = [('original_repositories', 'Original repositories'), ('stars', 'Stars received'),
               ('public_commits', 'Public commits'), ('commits_last_12_months', 'Commits · last 12 months')]
    for i, (key, label) in enumerate(metrics):
        x, y = 28 + (i % 2) * 274, 104 + (i // 2) * 111
        color = '#72d9ff' if key in {'public_commits', 'commits_last_12_months'} else '#ebf3ff'
        body += txt(x, y, f'{s[key]:,}', 42, color, 700)
        body += txt(x, y+29, label, 14, '#9fb5d2')
    body += txt(28, 283, f"{s['followers']} followers · Public data · Repository forks excluded", 12, '#88a2c2')
    stamp = datetime.fromisoformat(s['updated_at'].replace('Z', '+00:00')).strftime('%d %b %Y · %H:%M UTC')
    body += txt(28, 313, 'Updated ' + stamp, 12, '#88a2c2')
    return panel('GitHub engineering snapshot', s['scope'], body, 560, 338)


def details_card(s, mobile=False):
    parts = []
    for i, card in enumerate([language_card(s), activity_card(s)]):
        prefix = f'card{i}-'
        for identity in re.findall(r'id="([^"]+)"', card):
            card = card.replace(f'id="{identity}"', f'id="{prefix}{identity}"')
            card = card.replace(f'url(#{identity})', f'url(#{prefix}{identity})')
        card = card.replace('aria-labelledby="title desc"', f'aria-labelledby="{prefix}title {prefix}desc"')
        x, y = (0, i * 389) if mobile else (i * 576, 0)
        parts.append(card.replace('<svg ', f'<svg x="{x}" y="{y}" ', 1))
    w, h = (560, 762) if mobile else (1136, 373)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Repository languages and monthly commit activity">' + ''.join(parts) + '</svg>'


def render(s, output):
    # Finish every rendering before changing any checked-in output.
    outputs = {'github-overview.svg': overview(s), 'github-languages.svg': language_card(s),
               'github-activity.svg': activity_card(s),
               'github-overview-mobile.svg': overview_mobile(s),
               'github-details.svg': details_card(s),
               'github-details-mobile.svg': details_card(s, mobile=True),
               'github-stats.json': json.dumps(s, indent=2, ensure_ascii=False) + '\n'}
    output.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        temporary = output / (name + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', default='zaidmoen')
    parser.add_argument('--from-snapshot', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'assets' / 'stats')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', args.user):
        parser.error('Invalid GitHub username')
    snapshot = json.loads(args.from_snapshot.read_text()) if args.from_snapshot else fetch_snapshot(args.user)
    render(snapshot, args.output)
    print(f"Rendered public statistics for {snapshot['user']} at {snapshot['updated_at']}")


if __name__ == '__main__':
    main()
