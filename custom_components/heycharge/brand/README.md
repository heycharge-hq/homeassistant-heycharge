# Brand Assets

These PNGs are the canonical brand images for the HeyCharge integration.
Home Assistant 2026.3+ serves them via its Brands Proxy API at
`/api/brands/integration/heycharge/<filename>`, and HACS reads them from
this directory when displaying the integration in its catalog.

This is the ONLY place these images need to live. PRs to
`home-assistant/brands` are no longer accepted for new custom
integrations (per the [Brands Proxy API
announcement](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/)).

## Files

| File             | Dimensions | Purpose                                    |
|------------------|-----------:|--------------------------------------------|
| `icon.png`       |    256×256 | Square app icon, light backgrounds         |
| `icon@2x.png`    |    512×512 | Hi-DPI variant of `icon.png`               |
| `logo.png`       |   1024×256 | Full wordmark, light backgrounds           |
| `logo@2x.png`    |   2048×512 | Hi-DPI variant of `logo.png`               |
| `dark_logo.png`  |   1024×256 | White-on-transparent for dark backgrounds  |
| `dark_logo@2x.png` | 2048×512 | Hi-DPI variant of `dark_logo.png`          |

All PNGs are RGBA, transparency-preserving. Brand spec for
"shortest side" is 128–256 px (`logo`) and 256–512 px (`logo@2x`); we
ship at the maximum to keep quality on hi-DPI displays.

## Re-rendering from sources

Source SVGs live in `homeassistant/assets/`. Icons are hand-crafted
square PNGs (no SVG source); only the wordmark logos regenerate from
SVG:

```bash
cd homeassistant/integration/custom_components/heycharge/brand
rsvg-convert -h 256 "../../../../../assets/hey charge_logo color (1).svg"   -o logo.png
rsvg-convert -h 512 "../../../../../assets/hey charge_logo color (1).svg"   -o logo@2x.png
rsvg-convert -h 256 "../../../../../assets/hey charge_logo white alpha.svg" -o dark_logo.png
rsvg-convert -h 512 "../../../../../assets/hey charge_logo white alpha.svg" -o dark_logo@2x.png
```

Requires `rsvg-convert` (`brew install librsvg`).
