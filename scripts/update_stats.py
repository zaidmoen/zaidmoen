"""Fetch public GitHub metrics and render repository-hosted profile cards.

Python 3.10+; standard library only. Errors abort before replacing output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
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


def fetch_commit_activity(user: str, original: list[dict], months: list[str], now: datetime):
    """Collect monthly and daily authored commit counts from default-branch history."""
    end = now.date()
    start = end - timedelta(days=364)
    since = min(f'{months[0]}-01', start.isoformat()) + 'T00:00:00Z'
    window = set(months)
    monthly, daily, repositories = Counter(), Counter(), Counter()
    for repo in original:
        page = 1
        while True:
            query = urlencode({'author': user, 'since': since, 'per_page': 100, 'page': page})
            try:
                batch = api(f'/repos/{user}/{repo["name"]}/commits?{query}')
            except HTTPError as error:
                if error.code == 409:
                    break
                raise
            if not batch:
                break
            for commit in batch:
                value = (commit.get('commit') or {}).get('author', {}).get('date')
                if not value:
                    continue
                day = datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc).date()
                if day > end:
                    continue
                key = day.isoformat()
                if key[:7] in window:
                    monthly[key[:7]] += 1
                if start <= day <= end:
                    daily[key] += 1
                    repositories[repo['name']] += 1
            if len(batch) < 100:
                break
            page += 1
    days = [{'date': (start + timedelta(days=i)).isoformat(),
             'count': daily[(start + timedelta(days=i)).isoformat()]} for i in range(365)]
    return ([{'month': month, 'count': monthly[month]} for month in months], days,
            [{'name': name, 'count': count}
             for name, count in sorted(repositories.items(), key=lambda p: (-p[1], p[0]))])


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
    monthly, daily, active_repositories = fetch_commit_activity(user, original_repos(user, repos), months, now)
    snapshot = summarize(user, repos, profile['followers'], public_commits, monthly, now)
    snapshot.update(daily_commits=daily, active_repositories=active_repositories)
    return snapshot



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



# Calendar metrics are derived from a complete rolling daily snapshot, never from monthly estimates.
HEAT_COLORS = ('#18212C', '#303C65', '#5062A5', '#8294ED', '#4FD1C5')


def calendar_summary(days):
    active = sum(item['count'] > 0 for item in days)
    longest = streak = 0
    for item in days:
        streak = streak + 1 if item['count'] > 0 else 0
        longest = max(longest, streak)
    return {'total': sum(item['count'] for item in days), 'active': active,
            'longest': longest, 'peak': max((item['count'] for item in days), default=0)}


def calendar_svg(s, mobile=False):
    width, height = (560, 695) if mobile else (1120, 465)
    parts = []

    def text(x, y, value, size=14, color='#F5F7FA', weight=400, mono=False, anchor='start'):
        font = 'Consolas,Liberation Mono,monospace' if mono else 'Arial,Helvetica,sans-serif'
        parts.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rect(x, y, w, h, fill='#11161D', stroke='none', radius=5):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def line(x1, y, x2):
        parts.append(f'<path d="M{x1} {y}H{x2}" fill="none" stroke="#242D3A"/>')

    def finish(h, description):
        body = ''.join(parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" role="img" aria-labelledby="title desc">'
                f'<title id="title">Public commit activity calendar</title><desc id="desc">{escape(description)}</desc>{body}</svg>')

    days = s.get('daily_commits')
    if not days:
        rect(.5, .5, width-1, 124, '#0B0F14', '#242D3A', 12)
        text(24, 35, '❯ git activity --calendar', 14, '#9AA7FF', 600, True)
        text(24, 66, 'Daily history not yet available', 20, weight=600)
        text(24, 91, 'The next successful statistics refresh will populate this calendar.', 13, '#98A2B3')
        return finish(125, 'Daily history is not available in this snapshot.')

    first = datetime.strptime(days[0]['date'], '%Y-%m-%d').date()
    last = datetime.strptime(days[-1]['date'], '%Y-%m-%d').date()
    if len(days) != 365 or any(datetime.strptime(item['date'], '%Y-%m-%d').date() != first + timedelta(days=i)
                               or not isinstance(item['count'], int) or item['count'] < 0
                               for i, item in enumerate(days)):
        raise ValueError('Invalid daily commit snapshot: expected 365 consecutive nonnegative daily counts')
    summary = calendar_summary(days)
    rect(.5, .5, width-1, height-1, '#0B0F14', '#242D3A', 12)
    rect(12, 12, width-24, 38, '#151B25', '#242D3A', 7)
    text(26, 36, '❯ git activity --calendar', 14, '#9AA7FF', 600, True)
    text(width-26, 36, '365 DAYS / UTC', 10, '#98A2B3', mono=True, anchor='end')
    text(24, 88, f"{summary['total']:,} commits in the last 365 days", 24 if mobile else 28, weight=700)
    text(25, 111, 'Owned, original public repositories · authored commits', 12, '#98A2B3')
    offset = (first.weekday() + 1) % 7
    weeks = (offset + len(days) + 6) // 7
    cell, pitch, origin_x = (14, 17, 57) if mobile else (15, 19, 62)

    def draw_block(start_week, end_week, y):
        last_label_x = -100
        for row, label in ((1, 'Mon'), (3, 'Wed'), (5, 'Fri')):
            text(24, y + row*pitch + cell-3, label, 10, '#98A2B3', mono=True)
        for i, item in enumerate(days):
            week, row = divmod(offset+i, 7)
            if not start_week <= week < end_week:
                continue
            x = origin_x + (week-start_week)*pitch
            yy = y + row*pitch
            day = first + timedelta(days=i)
            n = item['count']
            level = 0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 10 else 4
            parts.append(f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="3" fill="{HEAT_COLORS[level]}"><title>{item["date"]}: {n} commits</title></rect>')
            if (day.day == 1 or i == 0 or (week == start_week and row == 0)) and x-last_label_x >= 35:
                text(x, y-9, day.strftime('%b'), 11, '#98A2B3', mono=True)
                last_label_x = x

    draw_block(0, min(27, weeks) if mobile else weeks, 143)
    if mobile:
        draw_block(27, weeks, 291)
    legend_y = 426 if mobile else 287
    text(24, legend_y+11, f'{first.isoformat()} — {last.isoformat()}', 11, '#98A2B3', mono=True)
    legend_x = width-176
    text(legend_x-7, legend_y+11, 'Less', 10, '#98A2B3', anchor='end')
    for i, color in enumerate(HEAT_COLORS):
        rect(legend_x+i*19, legend_y, 14, 14, color, radius=3)
    text(legend_x+99, legend_y+11, 'More', 10, '#98A2B3')
    divider_y = 451 if mobile else 310
    line(24, divider_y, width-24)
    metrics = [('ACTIVE DAYS', summary['active']), ('LONGEST STREAK', f"{summary['longest']}d"), ('BUSIEST DAY', f"{summary['peak']} commits")]
    if mobile:
        for i, (label, value) in enumerate(metrics):
            x = 24+i*174
            rect(x, 468, 164, 62, '#11161D', '#242D3A')
            text(x+10, 485, label, 9, '#98A2B3', mono=True)
            text(x+10, 514, value, 21, '#9AA7FF', 700)
        text(24, 558, 'TOP ACTIVE REPOSITORIES', 11, '#98A2B3', mono=True)
        for i, entry in enumerate(s.get('active_repositories', [])[:3]):
            y = 581+i*24
            text(24, y, entry['name'][:44], 13)
            text(width-24, y, f"{entry['count']} commits", 12, '#4FD1C5', anchor='end')
        text(24, 674, 'Daily intensity: 0 / 1–2 / 3–5 / 6–10 / 11+ commits', 11, '#98A2B3')
    else:
        text(24, 335, 'ACTIVITY OVERVIEW', 11, '#98A2B3', mono=True)
        for i, (label, value) in enumerate(metrics):
            x = 24+i*185
            rect(x, 349, 174, 70, '#11161D', '#242D3A')
            text(x+12, 368, label, 10, '#98A2B3', mono=True)
            text(x+12, 398, value, 23, '#9AA7FF', 700)
        parts.append('<path d="M590 324V435" stroke="#242D3A"/>')
        text(614, 335, 'TOP ACTIVE REPOSITORIES', 11, '#98A2B3', mono=True)
        for i, entry in enumerate(s.get('active_repositories', [])[:3]):
            y = 358+i*24
            text(614, y, entry['name'][:44], 14)
            text(width-24, y, f"{entry['count']} commits", 12, '#4FD1C5', anchor='end')
        text(24, 445, 'Daily intensity: 0 / 1–2 / 3–5 / 6–10 / 11+ commits', 11, '#98A2B3')
    return finish(height, f"{summary['total']} authored commits, {summary['active']} active days, {summary['longest']} day longest streak. Public original owned repositories only, not the complete GitHub contributions graph.")



def render(s, output):
    # Finish every rendering before changing any checked-in output.
    outputs = {'github-overview.svg': overview(s), 'github-languages.svg': language_card(s),
               'github-activity.svg': activity_card(s),
               'github-overview-mobile.svg': overview_mobile(s),
               'github-details.svg': details_card(s),
               'github-details-mobile.svg': details_card(s, mobile=True),
               'github-calendar.svg': calendar_svg(s),
               'github-calendar-mobile.svg': calendar_svg(s, mobile=True),
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
