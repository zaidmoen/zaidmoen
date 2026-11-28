# Terminal Identity / Zaid Mayyalleh

**Building what comes next.**

A modern terminal-inspired identity with strong typography, restrained motion, and a small conceptual system map.

| Role | Color |
| --- | --- |
| Background | `#0B0F14` |
| Panel | `#11161D` |
| Primary text | `#F5F7FA` |
| Secondary text | `#98A2B3` |
| Border | `#242D3A` |
| Periwinkle | `#9AA7FF` |
| Teal | `#4FD1C5` |

Use system sans-serif for names and descriptions; monospace for commands, metadata and labels. Keep motion limited to the hero. Desktop and mobile artwork are separate SVG files in `assets/terminal/`. Prior identities remain in the repository for reference. The account avatar is unchanged.

The statistics renderer uses the matching palette. Regenerate from the existing snapshot with:

```bash
python3 scripts/update_stats.py --from-snapshot assets/stats/github-stats.json
```

The legacy artwork generator is not needed for the active terminal identity.
