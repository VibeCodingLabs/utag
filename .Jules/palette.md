## 2024-07-10 - Accessible SVG Animations in Markdown
**Learning:** When using animated SVGs directly in GitHub READMEs, user settings like 'prefers-reduced-motion' aren't always reliably passed down to the `<img>` tag in markdown rendering, potentially causing accessibility issues with motion sickness.
**Action:** Use CSS inside the SVG for `@media (prefers-reduced-motion: reduce)`, but ALSO ensure the default animation is slow (`12s`) and subtle (`ease-in-out`), avoiding rapid flashing or moving patterns as a fail-safe.
