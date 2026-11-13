# Design tokens

The only values the UI may use. Proposal — edit freely; once agreed, anything not
listed here needs sign-off. Starting point is the identity the site already has
(clover green, cream, Cinzel), minus the stock blue/indigo/purple that crept in.

## Principles

1. One accent colour. Clover green does the work blue does today.
2. Separate with space and hairlines, not shadows and cards.
3. No gradients, no emoji as icons, no decorative animation.
4. Two typefaces, self-hosted.
5. Mobile first: every value below is the 360 px value unless it says otherwise.

## Colour

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#F5F5DC` cream | `#111814` | Page background |
| `--surface` | `#FBFBEF` | `#1A231D` | Inputs, result panels |
| `--text` | `#1C1F1A` | `#ECEFE6` | Body text |
| `--text-muted` | `#5A6156` | `#A3AB9D` | Descriptions, metadata |
| `--border` | `#D5D8C4` | `#2E3A31` | Hairlines, input borders |
| `--accent` | `#1B5E37` clover dark | `#7FC796` | Links, primary button, focus ring |
| `--accent-hover` | `#145029` | `#9AD8AE` | Hover / pressed |
| `--accent-soft` | `#3D8B4F` clover mid | `#3D8B4F` | Large headings and icons only |
| `--highlight` | `#9ACD32` clover lime | `#9ACD32` | Decoration only, never text |
| `--ok` / `--warn` / `--bad` | `#15803D` / `#92400E` / `#B91C1C` | `#4ADE80` / `#FBBF24` / `#F87171` | Resume analysis: matching / related / missing |

Contrast (hand-calculated, verify with a checker): `--accent` on `--bg` ≈ 7:1, fine
for text. `--accent-soft` on `--bg` ≈ 3.8:1, so large text and icons only.
`--highlight` fails for text on cream.

Removed: `#3B82F6`, `#2563EB`, `#60A5FA` (blues), `#6366F1`, `#818CF8` (indigo),
purple headings on the questions section.

## Type

| Token | Value | Use |
|---|---|---|
| `--font-display` | Cinzel, Georgia, serif | Logo, page title, box headings |
| `--font-text` | DECIDE: a text serif (e.g. Source Serif 4) or system UI sans | Everything else |
| `--text-sm` | 0.875rem / 1.4 | Metadata |
| `--text-base` | 1rem / 1.5 | Body, inputs (never below 16 px: iOS zooms otherwise) |
| `--text-lg` | 1.125rem / 1.4 | Link titles |
| `--text-xl` | clamp(1.25rem, 1rem + 1.2vw, 1.5rem) / 1.25 | Box headings |
| `--text-2xl` | clamp(1.6rem, 1.2rem + 2vw, 2.25rem) / 1.15 | Page title |

Weights: 400 and 700 only. Cinzel is capitals-only, so keep it to short headings.
Today body text is Times New Roman; decide whether to keep that character or move
to a face drawn for screens.

## Space, shape, motion

| Token | Value |
|---|---|
| `--space-1 … --space-6` | 4, 8, 12, 16, 24, 40 px |
| `--gutter` | 16 px (24 px from 768 px up) |
| `--measure` | 68ch max line length |
| `--radius` | 4 px (inputs, buttons). Nothing larger. |
| `--border-width` | 1 px |
| `--shadow` | None by default. One allowed: dropdown/modal `0 4px 16px rgb(0 0 0 / .12)` |
| `--tap` | 44 px minimum height for anything tappable |
| `--ease` | 150 ms ease-out, colour and opacity only; off under `prefers-reduced-motion` |

## Layout

- One column up to 768 px. Boxes stack in order 1–4.
- From 768 px: two columns of boxes. From 1200 px: content max-width 1120 px.
- Search form: stacked fields on mobile, submit button full width.

## Components (the whole list)

Search field with autocomplete · button (primary, quiet) · box (heading + sections) ·
section (heading + links; dropdown in box 4) · link row (title, site, description) ·
video row · loading skeleton · empty state · error state · modal · theme toggle.

## Icons

One outline set (DECIDE: Lucide or Phosphor), 20 px, `currentColor`.

## Dark mode

Follows the system setting by default; the toggle overrides and is remembered.

## Decisions needed from you

1. Text typeface.
2. Icon set.
3. Keep cream as the background, or go near-white with cream as an accent surface?
4. Is the lime highlight still wanted anywhere?
