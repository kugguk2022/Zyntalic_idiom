# Zyntalic — Polyglot Arc

The repository identity is **Polyglot Arc**, selected on 13 November 2026 from
the supplied Zyntalic animated-logo directions. The production SVG concentrates
direction **1e** into a compact mark: two intersecting language orbits, the
existing angular Zyntalic sigil, and one rising signal arc. The larger mark also
carries two source glyphs and paired waves.

![Zyntalic Polyglot Arc](../zyntalic-flow/public/brand/zyntalic-lockup.svg)

## Assets

The SVG files are the editable source assets. No build step, font installation,
JavaScript, network request, or embedded bitmap is required to display them.

| File | Use |
| --- | --- |
| [zyntalic-logo.svg](../zyntalic-flow/public/brand/zyntalic-logo.svg) | Transparent primary mark for dark backgrounds; use at 96 px or larger. |
| [zyntalic-logo-light.svg](../zyntalic-flow/public/brand/zyntalic-logo-light.svg) | Transparent primary mark with dark ink and deeper colors for light backgrounds. |
| [zyntalic-logo-mono.svg](../zyntalic-flow/public/brand/zyntalic-logo-mono.svg) | Single-color version. Edit the root `color` attribute, or set `color` when embedding the SVG inline. |
| [zyntalic-logo-animated.svg](../zyntalic-flow/public/brand/zyntalic-logo-animated.svg) | Optional dark-background motion mark. A highlight travels along the arc over six seconds while the complete base mark remains visible. |
| [zyntalic-lockup.svg](../zyntalic-flow/public/brand/zyntalic-lockup.svg) | Static emblem and outlined ZYNTALIC wordmark on a dark tile. The default README artwork works on light and dark page backgrounds. |
| [favicon.svg](../zyntalic-flow/public/favicon.svg) | Optically simplified tile for the browser icon and small app header. Stronger strokes, closer framing, and no miniature glyphs or waves. |

The animated SVG uses a CSS `prefers-reduced-motion: reduce` rule to suppress
the moving highlight. Renderers that ignore animation still receive the complete
static mark. Use the static asset in documents and repository previews where
motion support is uncertain. The app header and favicon use the static icon.

All wordmark lettering and decorative glyphs are vector paths. The primary mark
has genuine transparency; the lockup and favicon intentionally include a dark
background. Keep the aspect ratio, preserve the viewBox padding, and use the
small icon below 96 px rather than shrinking the detailed mark.

## Why this direction

- **1a, Convergence:** the strongest original small silhouette; its nucleus is
  retained, with fewer intersections and stronger proportions.
- **1b, Signal Arc:** supplies the directed signal and the upward sweep.
- **1c, Polyglot Orbit:** supplies the idea of a signal connecting scripts.
- **1d, Transcription Helix:** remains a visual direction for biology-related
  illustrations; it is not the general project mark.
- **1e, Polyglot Arc:** combines the useful parts of 1b and 1c around a stable
  Convergence core. Captions, particle fields, and font-dependent character
  clouds belong in larger illustrations rather than the compact logo.

The palette preserves cyan `#22d3ee` and blue `#4f7cff`, with violet `#a078ff`
and pale ink `#edfaff` tuned for the production mark. Light-background artwork
uses deeper cyan, blue, and violet. The symbol is decorative branding; it does
not assert additional language-engine or biological capabilities.

## Integration

The React header and browser icon already reference `/favicon.svg`. The FastAPI
service exposes that route, and the legacy HTML now references it explicitly.
No frontend component, Python route, translator, dependency, or generated output
was changed for the identity update.

Vite copies `public/brand/` into its build output. The existing FastAPI service
does **not** expose a general `/brand/` route, so the application continues using
`/favicon.svg`. README and documentation links refer to repository assets. A
future deployment that uses the larger files must deliberately serve them.

## Provenance

Source: the owner-supplied **Zyntalic animated logo directions – Zyntalic Animated
Logo (2).html**. Its final section names 1e **Polyglot Arc**. The source's five
directions are Canvas 2D animations; its small inline SVG is only a loading
thumbnail. These files are an intentional vector adaptation, not a claimed
export of an SVG that was present in that attachment.

Source attachment SHA-256:

```text
7924a43958f413fc6382408536288da60fbc11ec0dd649d41883a34e5ddf9aab
```

Vector adaptation and selection: ChatGPT, 13 November 2026, following the owner's
request to choose a stronger SVG and add it to the repository. Source sigils and
the Convergence/Polyglot Arc direction were retained. The precise author of the
supplied HTML is not established by the attachment. The wordmark is custom path
geometry; the attachment's bundled fonts are not redistributed.

This is a repository branding choice, not a claimed multi-provider vote. The
collaborative inquiry's existing candidate files, hashes, manifests, and ballots
remain separate records.

## Visual verification

![Primary mark on dark and light backgrounds, monochrome mark, lockup, and small icon sizes](images/zyntalic-brand-preview.png)

The final SVGs were parsed as XML and rendered offline. The primary mark was
inspected on dark and light backgrounds, and the simplified icon at 16, 24, 32,
36, and 64 pixels. Each file was checked for missing internal references,
external resources, scripts, raster content, and font dependencies.

The actual FastAPI application was exercised through its in-process test client:
`/favicon.svg` and `/favicon.ico` both returned HTTP 200, the `image/svg+xml`
content type, and the exact new icon bytes. The legacy root page returned HTTP
200 with the SVG icon reference. The source checkout was used without a Vite
build; no full application regression or frontend build result is claimed here.

The motion SVG's static fallback and reduced-motion CSS were inspected. Browser
motion playback could not be exercised in the execution environment because
Chromium startup was denied a required socket operation. No browser playback
result is implied by the static preview.
