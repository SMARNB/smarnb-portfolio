# Blender → site export spec (3D redesign)

Follow this when exporting any model for the site. If a file meets this spec it is a
drop-in replacement: copy it to `frontend/public/assets/models/`, update the `src`
(and `poster`) props on the `<ModelStage>` that shows it, done.

## Hard requirements

| What | Requirement | Why |
|---|---|---|
| Format | **glTF 2.0 Binary (`.glb`)**, single file | One request; loader expects it |
| Compression | **Draco ON** (Blender export → Geometry → Compression, level 6) | 3–8× smaller meshes; decoder already vendored at `/assets/draco/1.5.7/` |
| Size budget | **< 1.5 MB per .glb** (aim < 800 KB for the hero) | Free-tier bandwidth + mobile |
| Poly budget | Low-poly: **< 50k triangles** per model (hero: < 25k) | Steady 60 fps on mid phones |
| Lighting | **Bake lighting + AO into the base-color texture** (or a separate AO map baked in). No light objects in the export | The site renders with 3 plain lights, no HDR environment (CDN-free rule) |
| Textures | **Power-of-two sizes** (512/1024/2048; 1024 is the sweet spot), embedded in the .glb, **JPEG or WebP for color, keep total texture weight inside the size budget** | GPU mipmapping requires PoT; textures dominate file size |
| Materials | Principled BSDF only (maps to glTF PBR). No procedural nodes left unbaked — bake them to textures | Anything not baked silently drops on export |
| Animations | None for v1 (the site spins/drag-rotates the whole model) | Keeps files small |
| Cameras/extras | Delete cameras, lights, empties, hidden collections before export | They export as junk nodes |

## Orientation, origin & scale

- **Origin at the model's visual center** (Object → Set Origin → Center of Mass), model
  sitting roughly symmetric around it — the site auto-centers via bounding box, but a
  wild origin makes the spin look off-axis.
- **Face the front toward −Y in Blender** (Blender's front view). The glTF exporter's
  default "+Y up" conversion then shows the front to the site camera.
- **Scale is free** — the site normalizes the largest dimension automatically. Still,
  apply transforms before export (Ctrl+A → All Transforms) so nothing is skewed.

## Export checklist (Blender 4.x, File → Export → glTF 2.0)

1. Format: **glTF Binary (.glb)**
2. Include: Selected Objects (select only the model)
3. Transform: +Y Up (default)
4. Data → Mesh: Apply Modifiers ✓, Normals ✓, no vertex colors unless used
5. Data → Material: Materials = Export, Images = **Automatic**
6. **Compression ✓ (Draco), level 6**, position quantization 14, normal 10, texcoord 12
7. Name it **with a version**: `hero-v1.glb`, `hero-v2.glb`, … (never reuse a name —
   `/assets/*` is cached immutable by the server, so a changed file with the same
   name would stay stale for returning visitors)

## Poster render (required, one per model)

The poster is what no-WebGL / reduced-motion / crawler visitors see, and what shows
until the 3D chunk loads — the site never mounts three.js without one.

- Render the model in Blender from the same ¾ front angle, transparent background
  (Film → Transparent), ~1000×850 px.
- Export **WebP or PNG ≤ 60 KB** to `frontend/public/assets/img/`, e.g. `hero-v1-poster.webp`.

## Verifying an export before handing it over

- Drag the .glb into https://gltf-viewer.donmccurdy.com/ — if it looks right there
  (geometry, textures, no missing images), it will load on the site.
- Check the file size. If over budget: reduce texture resolution first (2048→1024
  usually halves the file), then Decimate modifier for polys.

## How the site consumes it (for reference)

```tsx
<ModelStage
  src="/assets/models/hero-v1.glb"        // Draco .glb, this spec
  poster="/assets/img/hero-v1-poster.webp" // Blender still render
  alt="What the model shows"
/>
```

- `ModelStage` (frontend/src/components/three/ModelStage.tsx): poster always renders;
  three.js is code-split and mounts only near the viewport on WebGL-capable,
  motion-OK devices; any failure falls back to the poster. Never blocks LCP.
- `ModelViewer` (…/three/ModelViewer.tsx): Draco decoding is first-party (decoder
  vendored in `frontend/public/assets/draco/1.5.7/`, pure-JS mode — no CDN, no extra
  CSP eval tokens). Lighting = 2 directionals + ambient + a cyan rim; bake anything
  fancier into textures.
- CSP note: the only header change for 3D is `worker-src 'self' blob:` (Draco decodes
  in a same-origin blob worker). `script-src` stays `'self'`.
