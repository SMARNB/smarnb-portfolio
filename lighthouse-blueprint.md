# Web Performance & Accessibility Optimization Blueprint (Desktop + Mobile)

## Context
I am optimizing a React/Vite application hosted on Render (`https://smarnb.onrender.com`). The application achieves high top-line scores but exhibits mobile network latency delays and explicit accessibility tree validation errors. I need Claude Code to refactor the codebase to address these cross-platform bottlenecks.

## Current PageSpeed Insights Core Metrics

### Desktop Summary
- **Performance:** 100/100 | **Accessibility:** 94/100 | **Best Practices:** 100/100 | **SEO:** 100/100
- **FCP / LCP:** 0.4s  | **TBT:** 10ms  | **Speed Index:** 0.7s

### Mobile Summary (Ref: image_dbfe96.png)
- **Performance:** 97/100  | **Accessibility:** 94/100 | **Best Practices:** 100/100 | **SEO:** 100/100
- **FCP / LCP:** 1.7s  | **TBT:** 20ms  | **Speed Index:** 4.1s

---

## Critical Bottlenecks & Code Fixes

### 1. Network & Bundle Loading (Mobile Priority)
On emulated mobile connections, asset sizes create delivery bottlenecks (Ref: image_dbfe7a.png, image_dbfe5c.png).
- **Render-Blocking CSS:** Lighthouse flags network styles delaying initial render with an **estimated savings of 300 ms** (`/assets/index-Cn93XLDC.css`).
  - *Task:* Audit how assets are being loaded in `index.html`. Add preloading strategies or optimize your CSS asset delivery so it doesn't halt the critical parsing path.
- **Unused JavaScript Payload:** `/assets/index-cB0Q--AS.js` carries **63.1 KiB** of dead/unused weight on initial execution.
  - *Task:* Introduce dynamic code-splitting. Use `React.lazy()` or dynamic `import()` components for hidden, secondary elements or lower-fold dashboard blocks so the main landing chunk stays lean.

### 2. Accessibility Tree Restructuring (Ref: image_dbfe00.png)
The site structure fails strict HTML validation rules, hurting screen readers and scoring tools alike.
- **Invalid Semantic Role Overrides:** Portfolio grid layout elements are utilizing `<article class="card work-card" role="button" tabindex="0">`. 
  - *Task:* An `<article>` element should never be overridden with an interactive button role. Convert the layout shell container to a clean structural wrapper (like a `<div>`) and place interactive actions onto actual semantic elements.
- **Prohibited Anchor States:** Social navigation links inside the footer employ `aria-disabled="true"` on operational generic anchor tags.
  - *Task:* Clean up elements like `<a class="social-empty" aria-disabled="true" aria-label="Instagram">`. Remove `aria-disabled` fields entirely for valid semantic web pointers.

### 3. Color Contrast Strategy (Ref: image_dbfe5c.png)
- **Contrast Ratios:** Essential headers, section blocks, utility tags (`.cat`, `.eyebrow`), and footer section markers (`<h4>INTERNATIONAL</h4>`, `<h4>SERVICES</h4>`, etc.) are dropping the global Accessibility metric down to 94.
  - *Task:* Adjust global CSS variables or local Tailwind templates (particularly text nodes drawing values from properties like `--muted-2`) to fulfill WCAG AA compliance ratios against their active background canvases.

### 4. Code Execution & Animations
- **Sequential Latency Waterfalls:** Your API architecture sequences queries progressively (`/` -> `index.js` -> `/api/testimonials` -> `/api/services`), elevating max latency chains towards 1,932 ms.
  - *Task:* Group component-level data dependency resolutions concurrently using mechanisms like `Promise.all` or independent parallel data requests.
- **Forced Reflow Thrashing:** Inlined bundle processes spend 56 ms triggering manual style invalidation recalculation loops.
  - *Task:* Hunt for synchronous geometric layout property evaluations (such as `.offsetWidth` or `.getBoundingClientRect()`) inside layout updates and convert them to non-blocking techniques.
- **Non-Composited Animations:** The active pulse element (`.status-pill .dot`) transitions structural styling rules (`box-shadow`), missing hardware GPU rasterization channels.
  - *Task:* Transition layout and structural element adjustments to high-performance composite layers (`transform`, `opacity`).

### 5. LLM Agent Interoperability (Ref: image_dbfe00.png)
- **llms.txt Specification Error:** The active discovery configuration file doesn't align with systemic crawler patterns.
  - *Task:* Re-format `/public/llms.txt`. Ensure the content starts cleanly with a prominent Markdown Level-1 header configuration (e.g., `# Syed Muhammad Ali Raza - Portfolio Context`) and explicitly maps visible navigation resource markers.

---

## Claude Code Execution Prompt
```bash
claude "Read and evaluate the architectural issues specified in our blueprint document. Proceed to refactor the project codebase sequentially: eliminate the render-blocking CSS delays, code-split our asset bundles, adjust typography contrast styles to fix the 94% accessibility limit, resolve the article role overrides, and optimize our root llms.txt structural markup."