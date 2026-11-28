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
COLORS = ["#9AA7FF","#4FD1C5","#C5CEFF","#8294C8","#62758F","#48566C"]


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



# Shared layout constants; only snapshot values and chart geometry are dynamic.
OVERVIEW_T = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1120\" height=\"258\" viewBox=\"0 0 1120 258\" role=\"img\" aria-labelledby=\"title desc\"><title id=\"title\">GitHub engineering dashboard</title><desc id=\"desc\">{{scope}} Updated {{updated_at}}.</desc><rect x=\"0.5\" y=\"0.5\" width=\"1119\" height=\"257\" rx=\"12\" fill=\"#0B0F14\" stroke=\"#242D3A\"/><rect x=\"12\" y=\"12\" width=\"1096\" height=\"42\" rx=\"7\" fill=\"#151B25\" stroke=\"#242D3A\"/><text x=\"28\" y=\"38\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"14\" fill=\"#9AA7FF\" font-weight=\"500\" >❯ git activity --summary</text><circle cx=\"981\" cy=\"33\" r=\"3.5\" fill=\"#4FD1C5\"/><text x=\"1092\" y=\"37\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">PUBLIC DATA</text><rect x=\"16\" y=\"70\" width=\"208\" height=\"132\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"29\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >01 / AUTHOR SEARCH</text><text x=\"28\" y=\"147\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"39\" fill=\"#9AA7FF\" font-weight=\"700\" >{{public_commits}}</text><text x=\"29\" y=\"173\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#98A2B3\" font-weight=\"400\" >Public commits</text><rect x=\"234\" y=\"70\" width=\"208\" height=\"132\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"247\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >02 / OWNED REPOS</text><text x=\"246\" y=\"147\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"39\" fill=\"#9AA7FF\" font-weight=\"700\" >{{commits_last_12_months}}</text><text x=\"247\" y=\"173\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#98A2B3\" font-weight=\"400\" >Commits · last 12 months</text><rect x=\"452\" y=\"70\" width=\"208\" height=\"132\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"465\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >03 / PUBLIC</text><text x=\"464\" y=\"147\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"39\" fill=\"#F5F7FA\" font-weight=\"700\" >{{original_repositories}}</text><text x=\"465\" y=\"173\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#98A2B3\" font-weight=\"400\" >Original repositories</text><rect x=\"670\" y=\"70\" width=\"208\" height=\"132\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"683\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >04 / REPOSITORIES</text><text x=\"682\" y=\"147\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"39\" fill=\"#F5F7FA\" font-weight=\"700\" >{{stars}}</text><text x=\"683\" y=\"173\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#98A2B3\" font-weight=\"400\" >Stars received</text><rect x=\"888\" y=\"70\" width=\"208\" height=\"132\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"901\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >05 / COMMUNITY</text><text x=\"900\" y=\"147\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"39\" fill=\"#F5F7FA\" font-weight=\"700\" >{{followers}}</text><text x=\"901\" y=\"173\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#98A2B3\" font-weight=\"400\" >Followers</text><path d=\"M16 215H1104\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"17\" y=\"237\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#4FD1C5\" font-weight=\"500\" >LAST SYNC</text><text x=\"108\" y=\"237\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >{{stamp}}</text><text x=\"1103\" y=\"237\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">GITHUB REST API / DAILY</text></svg>\n"
OVERVIEW_MOBILE_T = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"560\" height=\"450\" viewBox=\"0 0 560 450\" role=\"img\" aria-labelledby=\"title desc\"><title id=\"title\">GitHub engineering dashboard</title><desc id=\"desc\">{{scope}} Updated {{updated_at}}.</desc><rect x=\"0.5\" y=\"0.5\" width=\"559\" height=\"449\" rx=\"12\" fill=\"#0B0F14\" stroke=\"#242D3A\"/><rect x=\"12\" y=\"12\" width=\"536\" height=\"42\" rx=\"7\" fill=\"#151B25\" stroke=\"#242D3A\"/><text x=\"28\" y=\"38\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"14\" fill=\"#9AA7FF\" font-weight=\"500\" >❯ git activity --summary</text><circle cx=\"421\" cy=\"33\" r=\"3.5\" fill=\"#4FD1C5\"/><text x=\"532\" y=\"37\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">PUBLIC DATA</text><rect x=\"16\" y=\"70\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"29\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >01 / AUTHOR SEARCH</text><text x=\"28\" y=\"131\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#9AA7FF\" font-weight=\"700\" >{{public_commits}}</text><text x=\"29\" y=\"153\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Public commits</text><rect x=\"286\" y=\"70\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"299\" y=\"89\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >02 / OWNED REPOS</text><text x=\"298\" y=\"131\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#9AA7FF\" font-weight=\"700\" >{{commits_last_12_months}}</text><text x=\"299\" y=\"153\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Commits · last 12 months</text><rect x=\"16\" y=\"178\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"29\" y=\"197\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >03 / PUBLIC</text><text x=\"28\" y=\"239\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#F5F7FA\" font-weight=\"700\" >{{original_repositories}}</text><text x=\"29\" y=\"261\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Original repositories</text><rect x=\"286\" y=\"178\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"299\" y=\"197\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >04 / REPOSITORIES</text><text x=\"298\" y=\"239\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#F5F7FA\" font-weight=\"700\" >{{stars}}</text><text x=\"299\" y=\"261\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Stars received</text><rect x=\"16\" y=\"286\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"29\" y=\"305\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >05 / COMMUNITY</text><text x=\"28\" y=\"347\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#F5F7FA\" font-weight=\"700\" >{{followers}}</text><text x=\"29\" y=\"369\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Followers</text><rect x=\"286\" y=\"286\" width=\"258\" height=\"98\" rx=\"8\" fill=\"#11161D\" stroke=\"#242D3A\"/><text x=\"299\" y=\"305\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"9\" fill=\"#98A2B3\" font-weight=\"400\" >06 / WINDOW</text><text x=\"299\" y=\"347\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"25\" fill=\"#F5F7FA\" font-weight=\"600\" >12 months</text><text x=\"299\" y=\"369\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >Current month partial</text><path d=\"M16 399H544\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"17\" y=\"424\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#4FD1C5\" font-weight=\"500\" >LAST SYNC</text><text x=\"112\" y=\"424\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" >{{stamp}}</text><text x=\"543\" y=\"424\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">UTC</text></svg>\n"
ACTIVITY_T = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"560\" height=\"368\" viewBox=\"0 0 560 368\" role=\"img\" aria-labelledby=\"title desc\"><title id=\"title\">Monthly authored commits</title><desc id=\"desc\">Monthly default-branch commit activity in owned original public repositories. Current month is partial.</desc><rect x=\"0.5\" y=\"0.5\" width=\"559\" height=\"367\" rx=\"12\" fill=\"#0B0F14\" stroke=\"#242D3A\"/><text x=\"24\" y=\"31\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"13\" fill=\"#9AA7FF\" font-weight=\"500\" >❯ git log --monthly</text><text x=\"536\" y=\"31\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">12 MONTHS</text><path d=\"M24 45H536\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"24\" y=\"80\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#F5F7FA\" font-weight=\"700\" >{{total}}</text><text x=\"24\" y=\"101\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >authored commits in original public repos</text><text x=\"536\" y=\"77\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">PEAK MONTH</text><text x=\"536\" y=\"100\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"14\" fill=\"#4FD1C5\" font-weight=\"600\" text-anchor=\"end\">{{peak_label}}</text>{{grid}}{{bars}}<path d=\"M24 304H536\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"24\" y=\"327\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" >{{window}}</text><rect x=\"24\" y=\"339\" width=\"9\" height=\"9\" rx=\"2\" fill=\"#9AA7FF\" stroke=\"none\"/><text x=\"39\" y=\"348\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" >Completed month</text><rect x=\"171\" y=\"339\" width=\"9\" height=\"9\" rx=\"2\" fill=\"#172C31\" stroke=\"#4FD1C5\"/><text x=\"186\" y=\"348\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" >Current month · partial</text></svg>\n"
LANGUAGES_T = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"560\" height=\"368\" viewBox=\"0 0 560 368\" role=\"img\" aria-labelledby=\"title desc\"><title id=\"title\">Repository language distribution</title><desc id=\"desc\">Primary language per original public repository; percentages are not proficiency.</desc><rect x=\"0.5\" y=\"0.5\" width=\"559\" height=\"367\" rx=\"12\" fill=\"#0B0F14\" stroke=\"#242D3A\"/><text x=\"24\" y=\"31\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"13\" fill=\"#9AA7FF\" font-weight=\"500\" >❯ repo languages --share</text><text x=\"536\" y=\"31\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">BY REPOSITORY</text><path d=\"M24 45H536\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"24\" y=\"80\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"34\" fill=\"#F5F7FA\" font-weight=\"700\" >{{classified}}</text><text x=\"24\" y=\"100\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" >repositories with a detected primary language</text><text x=\"536\" y=\"78\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">TOP LANGUAGE</text><text x=\"536\" y=\"100\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"14\" fill=\"#4FD1C5\" font-weight=\"600\" text-anchor=\"end\">{{top_language}}</text>{{segments}}{{rows}}<path d=\"M24 304H536\" stroke=\"#242D3A\" fill=\"none\" /><text x=\"24\" y=\"327\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" >{{missing}} without a detected language</text><text x=\"24\" y=\"348\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"11\" fill=\"#98A2B3\" font-weight=\"400\" >Repository share, not lines of code or skill level.</text></svg>\n"
GRID_T = "<path d=\"M52 {{y}}H536\" stroke=\"#242D3A\" fill=\"none\" stroke-dasharray=\"3 5\"/><text x=\"43\" y=\"{{label_y}}\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">{{count}}</text>"
BAR_T = "<rect x=\"{{x}}\" y=\"{{y}}\" width=\"22\" height=\"{{height}}\" rx=\"3\" fill=\"{{fill}}\" stroke=\"{{stroke}}\" stroke-width=\"{{stroke_width}}\"><title>{{month}}: {{count}} commits</title></rect><text x=\"{{center}}\" y=\"{{value_y}}\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#F5F7FA\" font-weight=\"500\" text-anchor=\"middle\">{{value_label}}</text><text x=\"{{center}}\" y=\"285\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"10\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"middle\">{{label}}</text>"
SEG_T = "<rect x=\"{{x}}\" y=\"114\" width=\"{{w}}\" height=\"12\" fill=\"{{color}}\"><title>{{name}}: {{count}} repositories</title></rect>"
ROW_T = "<circle cx=\"29\" cy=\"{{dot_y}}\" r=\"4\" fill=\"{{color}}\"/><text x=\"42\" y=\"{{y}}\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"13\" fill=\"#F5F7FA\" font-weight=\"400\" >{{name}}</text><text x=\"536\" y=\"{{y}}\" font-family=\"ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace\" font-size=\"12\" fill=\"#98A2B3\" font-weight=\"400\" text-anchor=\"end\">{{count}} repos · {{pct}}%</text>"

def fill_template(template, **values):
    return re.sub(r'\{\{(\w+)\}\}', lambda m: str(values[m.group(1)]), template)


def _overview(s, mobile=False):
    keys = ('public_commits', 'commits_last_12_months', 'original_repositories', 'stars', 'followers')
    values = {key: f'{s[key]:,}' for key in keys}
    values.update(stamp=datetime.fromisoformat(s['updated_at'].replace('Z', '+00:00')).strftime('%d %b %Y · %H:%M UTC'),
                  scope=escape(s['scope']), updated_at=escape(s['updated_at']))
    return fill_template(OVERVIEW_MOBILE_T if mobile else OVERVIEW_T, **values)


def overview(s):
    return _overview(s)


def overview_mobile(s):
    return _overview(s, mobile=True)


def activity_card(s):
    points = s['monthly_commits']
    peak = max((p['count'] for p in points), default=0)
    base = 10 ** math.floor(math.log10(max(peak, 1)))
    step = next((x * base / 10 for x in (1, 2, 5, 10) if x * base / 10 >= peak / 3), base)
    scale = max(3, math.ceil(peak / step) * step)
    bottom, chart_height = 265, 132
    grid, bars = [], []
    for i in range(4):
        count = math.floor(scale * i / 3 + .5)
        y = bottom - chart_height * count / scale
        grid.append(fill_template(GRID_T, y=f'{y:.2f}', label_y=f'{y+3:.2f}', count=count))
    for i, point in enumerate(points):
        x = 64 + i * 39
        height = chart_height * point['count'] / scale
        y = bottom - height
        partial = i == len(points) - 1
        bars.append(fill_template(BAR_T, x=x, y=f'{y:.2f}', height=f'{height:.2f}',
                                  fill='#172C31' if partial else '#9AA7FF',
                                  stroke='#4FD1C5' if partial else 'none',
                                  stroke_width=1.5 if partial else 0, month=escape(point['month']),
                                  count=point['count'], center=x+11, value_y=f'{y-6:.2f}',
                                  value_label=point['count'] or '',
                                  label=datetime.strptime(point['month'], '%Y-%m').strftime('%b')))
    best = max(points[:-1], key=lambda p: p['count'], default=None)
    peak_label = f"{best['month']} / {best['count']}" if best and best['count'] else '—'
    window = f"{points[0]['month']} — {points[-1]['month']}" if points else 'No activity data'
    return fill_template(ACTIVITY_T, total=f"{s['commits_last_12_months']:,}", peak_label=escape(peak_label),
                         grid=''.join(grid), bars=''.join(bars), window=escape(window))


def language_card(s):
    langs = s['languages']
    display = langs[:5]
    if len(langs) > 5:
        display = display + [{'name': 'Other', 'repositories': sum(x['repositories'] for x in langs[5:])}]
    total = sum(x['repositories'] for x in langs)
    start, segments, rows = 24, [], []
    for i, entry in enumerate(display):
        count = entry['repositories']
        width = 512 * count / total if total else 0
        y = 151 + i * 25
        segments.append(fill_template(SEG_T, x=f'{start:.2f}', w=f'{width:.2f}',
                                      color=COLORS[i], name=escape(entry['name']), count=count))
        start += width
        rows.append(fill_template(ROW_T, dot_y=y-4, y=y, color=COLORS[i],
                                  name=escape(entry['name']), count=count,
                                  pct=f'{100 * count / total if total else 0:.1f}'))
    return fill_template(LANGUAGES_T, classified=total, top_language=escape(langs[0]['name']) if langs else '—',
                         segments=''.join(segments), rows=''.join(rows), missing=s['repositories_without_language'])


def details_card(s, mobile=False):
    parts = []
    for i, card in enumerate((activity_card(s), language_card(s))):
        prefix = f'card{i}-'
        card = re.sub(r'id="(title|desc)"', lambda m: f'id="{prefix}{m.group(1)}"', card)
        card = card.replace('aria-labelledby="title desc"', f'aria-labelledby="{prefix}title {prefix}desc"')
        x, y = (0, i * 384) if mobile else (i * 576, 0)
        parts.append(card.replace('<svg ', f'<svg x="{x}" y="{y}" ', 1))
    w, h = (560, 752) if mobile else (1136, 368)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Monthly commit activity and repository languages">' + ''.join(parts) + '</svg>'


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
