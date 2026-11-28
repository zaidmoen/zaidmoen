# Profile maintenance

The active profile uses **Terminal Identity**: dark blue-black surfaces, neutral typography, restrained periwinkle and teal accents. All active artwork is self-contained repository-hosted SVG. See [the identity guide](visual-identity.md).

## Statistics

The daily **Refresh profile statistics** workflow uses GitHub's REST API and the built-in `GITHUB_TOKEN`. No personal token or paid service is needed. It is scheduled for **05:23 UTC**; GitHub may delay scheduled runs. The Terminal Analytics dashboard shows the actual last successful refresh, not a live counter. Its five metric cards, monthly bar chart (current month outlined as partial) and repository-language distribution are visible directly in the README. The peak month is the highest completed month; it excludes the current partial month. Monthly counts use default-branch history from the per-repository commits endpoint. The rolling 365-day calendar is collected in the same API pass, and shows active days, the longest consecutive active-day streak and the busiest day. Its colors represent daily counts: 0, 1–2, 3–5, 6–10 and 11+. The daily calendar excludes private, forked and other-owned repositories, PRs, issues and reviews; it is deliberately not labeled as GitHub's full contribution graph. Dates are UTC. Older snapshots without daily history display a clear pending-refresh message instead of simulated activity.

| Metric | Definition |
| --- | --- |
| Original repositories | Public repositories owned by `zaidmoen`, excluding forks; archived repositories are included. |
| Stars received | Sum of stars on those original repositories. |
| Followers | The public follower count on the account. |
| Public commits | Commits returned by GitHub commit search for author `zaidmoen` in repositories visible publicly. |
| Commits · last 12 months | Commits authored by `zaidmoen` in owned, public, original repositories during the latest 12 calendar months. |
| Repository languages | One detected primary language per public original repository. Percentages use repositories with a detected language as the denominator. Repositories with no language are reported separately. These percentages are not proficiency, time spent, or lines of code. |
| Commit activity | Public authored commits in owned original repositories, grouped by month for the latest 12 calendar months. The current month is partial; zero months are retained. It is not a full contributions graph because private and forked repositories are excluded. |

The compact snapshot is saved in `assets/stats/github-stats.json`. API errors or incomplete search results cause the job to fail without publishing a partial refresh. Previous cards remain available with their original timestamp. GitHub search indexing can lag new commits.

### Run locally

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_stats.py
```

Python 3.10+ is enough; the generator uses only the standard library. A `GH_TOKEN` environment variable is optional locally and raises the GitHub API rate limit. Never put a token in the repository.

Render the committed snapshot without a network request:

```bash
python3 scripts/update_stats.py --from-snapshot assets/stats/github-stats.json
```

To refresh manually, open **Actions → Refresh profile statistics → Run workflow**. If the schedule is disabled by GitHub after repository inactivity, re-enable it there. A protected default branch may reject the bot's push; do not weaken protection to make the job run. In that case, change the refresh workflow to open a PR for generated assets.

## Artwork and motion

The active terminal hero, four project cards, and toolkit live in `assets/terminal/`, with desktop and mobile SVG variants. Edit them directly; the legacy generator (`scripts/build_artwork.mjs`) only rebuilds older artwork. The hero uses CSS-only cursor blink, entrance reveals and animated data paths; reduced-motion preferences disable these effects. No GIF, external fonts, JavaScript or external image service is used by the active profile. Prior artwork remains archived in its original directories.

## Content and links

The README highlights APEX FlowGuard (prototype), TelecomGuard AI (in development), NAI AI Hub, and Library Release Orchestrator (proof of concept). Earlier projects remain in the expandable project list. Project cards use conceptual labels, not fabricated metrics or screenshots. Contact links are unchanged.

Native Markdown/HTML navigation, links, and expandable details work within GitHub's README renderer. The language and activity breakdown is expandable to keep the default profile concise. Application frameworks such as React or Three.js do not execute inside a profile README.

Sources: [GitHub REST repository API](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user), [GitHub commit search API](https://docs.github.com/en/rest/search/search#search-commits), [scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [workflow token permissions](https://docs.github.com/en/actions/reference/authentication-in-a-workflow), and [reduced-motion preference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion).
