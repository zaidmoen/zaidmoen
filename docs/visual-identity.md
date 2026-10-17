# Zaid Mayyalleh / Visual identity

**Thoughtful systems. Built with intent.**

The identity pairs an angular ZM signature with generous space and a restrained gold accent. Its focus is backend engineering and applied AI, with clear project descriptions taking priority over decoration.

## Palette

| Role | Color | Usage |
| --- | --- | --- |
| Obsidian | `#101214` | Main background |
| Graphite | `#181B1E` | Illustration surfaces |
| Champagne | `#CDB583` | Monogram, labels and emphasis |
| Pale gold | `#E9D7AF` | Metallic highlight |
| Ivory | `#F3F0E9` | Main text |
| Silver | `#A7A9AA` | Supporting text |
| Slate | `#34383B` | Dividers and geometric construction |

Use gold sparingly on dark panels. The contact panel reverses the composition with dark text on gold. Do not place white text on the gold background.

## Signature

- [Monogram](../assets/brand/monogram.svg): a geometric Z and M in a diamond construction. Suitable for a square identity tile.
- [Wordmark](../assets/brand/wordmark.svg): the signature with the full name and engineering focus.
- Keep the mark's proportions. Maintain clear space of at least one stroke width around it.
- SVGs are self-contained and editable. The account avatar itself is not changed by this repository.

## Typography and composition

Use Arial or Helvetica for reliable SVG rendering. Large names and project titles use bold weights with tight spacing; small uppercase labels use wider tracking. Body text stays sentence case.

Desktop artwork uses a 1200-unit canvas with 48-unit margins. Mobile artwork uses 600 units with 32-unit margins. Project cards place descriptions above diagrams on mobile. Avoid shrinking desktop cards into mobile substitutes.

Native README headings, descriptions and links remain selectable and searchable. Images include descriptive alternatives. No important information relies on animation or color alone.

## Rebuild

```bash
node scripts/build_artwork.mjs
python3 scripts/update_stats.py --from-snapshot assets/stats/github-stats.json
```

The first command rebuilds all active artwork and the two brand assets. The second restyles the committed statistics without changing the measurements or their timestamp. The daily workflow uses the same statistics renderer.
