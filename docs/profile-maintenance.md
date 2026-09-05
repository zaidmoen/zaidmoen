# Profile maintenance

The profile combines a cinematic hero, native animated SVG artwork, and repository-hosted statistics. It does not load JavaScript, remote fonts, or third-party statistics images in the README.

## Statistics

The daily **Refresh profile statistics** workflow uses GitHub's REST API and the built-in `GITHUB_TOKEN`. No personal token or paid service is needed. It is scheduled for **05:23 UTC**; GitHub may delay scheduled runs. The overview shows the actual last successful refresh, not a live counter.

| Metric | Definition |
| --- | --- |
| Original repositories | Public repositories owned by `zaidmoen`, excluding forks; archived repositories are included. |
| Stars received | Sum of stars on those original repositories. |
| Followers | The public follower count on the account. |
| Pull requests opened | Public PRs authored by `zaidmoen`, across repositories. |
| Pull requests merged | Public authored PRs with merged status. |
| Repository languages | One detected primary language per public original repository. Percentages use repositories with a detected language as the denominator. Repositories with no language are reported separately. These percentages are not proficiency, time spent, or lines of code. |
| Pull request rhythm | Public authored PRs grouped by their creation month for the latest 12 calendar months. The current month is partial; zero months are retained. It is not a commits/contributions graph. |

The compact snapshot is saved in `assets/stats/github-stats.json`. API errors, incomplete search results, or search-window truncation cause the job to fail without publishing a partial refresh. Previous cards remain available with their original timestamp. GitHub search indexing can lag new PRs and merges.

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

## Motion and assets

- `assets/hero-cinematic.jpg`: the original cinematic artwork, optimized for delivery.
- `assets/motion-strip.svg`: orbital accent, a traveling light, and three rotating focus lines.
- `assets/project-*.svg`: gentle floating artwork and breathing light.
- `assets/connect.svg`: matching contact artwork.

SVG animation uses CSS keyframes inside the image. All decorative motion stops with `prefers-reduced-motion: reduce`; the first focus line remains readable. The static artwork is valid even if a viewer disables animation. External SVG resources and scripts are not required.

Edit SVGs as text. Keep useful `title`, `desc`, and README `alt` text. GitHub sanitizes README HTML, so application libraries such as React, GSAP, and Three.js cannot execute inside a profile README.

Sources: [GitHub REST repository API](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user), [GitHub search API](https://docs.github.com/en/rest/search/search#search-issues-and-pull-requests), [scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [workflow token permissions](https://docs.github.com/en/actions/reference/authentication-in-a-workflow), and [reduced-motion preference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion).
