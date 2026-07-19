# Zyvion Headquarters - Hybrid Architecture & Execution Blueprint

## 1. System Objective
You are the Lead Architect building the Zyvion 3D interactive storefront. The architecture consists of a React Three Fiber (R3F) frontend and a Node.js backend utilizing a Hybrid NPC Chatbot System. 
The system must minimize compute by routing basic interactions through frontend logic, and complex queries through a $0-cost API RAG backend.

## 2. Phase 1: Blender Asset Generation (via MCP)
Before writing any web code, use the `blender-mcp` tool to complete the 3D environment in the active Blender session.
**Rule:** You must ask me for design specifications for each item, wait for my reply, execute the `bpy` script, and ask for visual confirmation before moving to the next:
1.  **Basement Split:** Divide `Basement_Level` into Zone A (Gym/Pool) and Zone B (Cafeteria).
2.  **Vertical Transport:** Generate a central `Lift_Elevator` and `Stair_Cases` (Basement to floor .007).
3.  **Interior/NPCs:** Populate floors with distinct low-poly props. Place capsule-based NPCs assigned to roles: Lobby Greeter, Gate Auth, and Portfolio Reps.
4.  **Roof & Exterior:** Generate a Helipad, external road, perimeter gates, and parked cars.
5.  **Export:** Export the scene as `zyvion_hq.glb` to the web project's `/public/models/`.

## 3. Phase 2: Frontend Scaffold (React Three Fiber)
Initialize the Vite React TypeScript project. 
*   **Dependencies:** `three`, `@react-three/fiber`, `@react-three/drei`, `gsap`, `@gsap/react`, `zustand`.
*   **Store (`useStore.ts`):** Track `activeNPC` (string | null), `languagePreference` ('en' | 'ur'), and a dictionary of `npcData`.
*   **Canvas Logic:** Implement `OfficeScene.tsx` (GSAP scroll-build logic) and `CameraController.tsx` (toggle First-Person vs. Isometric).

## 4. Phase 3: The Hybrid NPC UI & Router
Create `InteractableNPC.tsx` (3D raycasting) and `NPCChatInterface.tsx` (HTML DOM overlay with English/Urdu toggle and chat history).
**The Hybrid Router Logic:**
*   `npcData` must define `type: 'deterministic' | 'generative'`. 
*   If a user interacts with a 'deterministic' NPC (Lobby Greeter, Gate Auth), handle the response entirely in the React frontend using a hardcoded decision tree.
*   If a user interacts with a 'generative' NPC (Portfolio Rep), send the query to the Node.js backend.

## 5. Phase 4: Zero-Cost RAG Backend 
Initialize a `server/` directory for the Express.js backend.
*   **Dependencies:** `express`, `cors`, `langchain`, `@langchain/community`, `@langchain/google-genai`, `chromadb`.
*   **The Architecture:**
    1.  **Vector DB:** Set up a local ChromaDB instance to store document embeddings.
    2.  **Embeddings API:** Integrate the Google Gemini Embedding API (`gemini-embedding-001`) to vectorize the project READMEs. 
    3.  **Inference API:** Integrate the Hugging Face Inference API (`@huggingface/inference`) to query an open-source model (e.g., Llama-3-8B-Instruct).
*   **API Endpoint (`POST /api/chat`):** Extract the `npcId`, `userMessage`, and `languagePreference`. Retrieve relevant context from Chroma, construct a strict bilingual prompt, query the Hugging Face API, and return the response to the frontend.
*   **Ingestion Script:** Provide a standalone `ingest.js` to process my Markdown files into Chroma using the Gemini Embeddings API.

## 6. Execution Command
Acknowledge these instructions, activate the `blender-mcp` tool, and initiate Phase 1 by asking me for the Basement Split design requirements.

---

## 7. As-Built Log (Phase 1.1 + 1.2 — completed 2026-07-16, branch `feat/zyvion-hq-3d`)

### Execution bridge (supersedes "blender-mcp" above)
The stock MCP server on port 9876 starves when Blender idles — **do not use it**. Scripts run through the custom listener: `POST http://localhost:5000/execute` (raw Python, `text/plain`). Contract every script must follow:
1. Wrap ALL code in one function (the listener execs with split globals/locals — top-level defs can't recurse, module imports invisible in function bodies).
2. Register the function via `bpy.app.timers.register(fn)` — **never mutate `bpy.data` on the listener thread** (crashes Blender on next redraw; caused one crash on 2026-07-16).
3. The listener returns only a success string: scripts write results as JSON to the session scratchpad, which the agent polls (fresh `LastWriteTime` only).
4. Scripts are idempotent: kill-by-name before create; all transforms are absolute values derived from ORIGINAL analysis numbers × `SXY` (stored in `scene["zy_plinth"]` / `scene["zy_ground"]`).

### Pipeline scripts (run in order)
1. `scripts/phase1_1_basement_split.py` — site + basement + tower massing
2. `scripts/phase1_2_vertical_transport.py` — core shaft + wrap stairs (re-splits plinth/ceiling around the core)
3. `scripts/phase1_1_render_preview.py` — confirmation renders to the scratchpad

### As-built design (deviations from §2 are user-directed)
- **Scale:** `SXY = 2.5` — establishment footprint 40×40 → **100×100 m**; the whole site (ground, grassland + its stairs/walls, gatehouse) scales with it. Floors are **20 ft (H = 6.1 m)**; Grand Lobby = 4 floors (24.4 m); guard house (`Enternace_Area`) and **all perimeter fences = 20 ft**.
- **Plinth:** the original `Basement_Level` block is a solid elevation **spacer** (z 5.42–9.23), rebuilt as pieces with two entry portals; original object kept as `_Legacy_Backup/Building_Plinth_ORIGINAL`.
- **Basement (underground, z −0.67..5.43):** Zone_A_Gym_Pool (west 60%: 16×8 recessed pool, gym equipment) | Zone_B_Cafeteria (east 40%: 3 food-court stalls, mixed seating). **The wings are TOTALLY ISOLATED — no internal connection, by explicit instruction.** Divider is solid, floor-to-ceiling, at `x0 + 0.6·width`.
- **Entries (carved INTO the plinth, nothing outside the footprint):** west = centered 6 m grand staircase descending to the gym; east = sidewise 2 m staircase along the east wall descending to the cafeteria.
- **Vertical core (Phase 1.2):** 8×8 at x −4..4, y 1..9 — inside the `Cubicle_Workspace` column on every level, clear of the lobby. Glass panoramic lift (`ZY_Glass_Blue`, alpha 0.32) with door frames at basement + 8 levels and the cab parked in the basement; **square-helix stairs wrap the shaft** with a flat amber landing at each lift door. Core serves the **gym wing only** (cafeteria stays isolated). The 8 `Cubicle_Workspace` levels were rebuilt as 4-piece rings (originals retired to `_Legacy_Backup`).
- **Materials:** 15 flat `ZY_*` materials (viewport colors set for Solid mode) — the palette for the GLB/R3F pipeline.
- **Collections:** `Basement_Level/{Basement_Shell, Zone_A_Gym_Pool, Zone_B_Cafeteria}`, `Building_Plinth`, `Site_Ground`, `Vertical_Core`, hidden `_Legacy_Backup`.

---

## 8. As-Built Log (Phase 1.3 — completed 2026-07-18, branch `feat/zyvion-hq-3d`)

~5,000 objects. Same bridge contract as §7 (POST :5000, single wrapper + `bpy.app.timers`, JSON status to the scratchpad, idempotent kill-by-name / prefix sweeps).

### Pipeline order (MANDATORY — prefix-sweep dependencies)
`phase1_3_grand_lobby.py` → `phase1_3_lobby_services.py` → `phase1_3_west_wing.py` → `phase1_3_east_wing.py` → `phase1_3_rear_blocks.py` → `phase1_3_wing_floors.py` → `phase1_3_center_floors.py` → `phase1_3_rooftop.py` → `phase1_3_site.py` → `phase1_3_gates_guard.py`, then `phase1_3_render_preview.py` (27 views).
The lobby sweep clears `Lobby_*`; the wings re-split `Lobby_Wall_W/E`; rear re-splits `Lobby_Wall_N`; `wing_floors` sweeps the `*Stack*` upper levels; `gates_guard` sweeps `Fence_S_/Gate_/GRoom_/Sec_`. Running out of order silently drops openings.

### As-built
- **Grand Lobby = About page.** Hollow 4-story atrium; glass curtain south façade with a 12×9 m open portal + canopy; U-shaped mezzanine rings at levels 2/3/4 with glass rails and a hero-screen notch. **No inter-floor stairs in the lobby** (user-removed); mezzanines are reached from the wing stair shafts. Raycast targets: `Lobby_Display_About_1..6`, `Lobby_Display_Hero`, `NPC_Lobby_Greeter` (custom props `npc_id`/`npc_type=deterministic`/`npc_role`). Services: "Halo" 3-tier ring chandelier, exposed loop duct + slot diffusers, colour-coded cable trays (amber=power, teal=data, red=security), 3 couches.
- **West wing L1 = Waiting Room:** cubicles + public PC counter (split around the lobby doorway), sealed glass coffee bar, M/W restrooms, west exit + façade stair. **East wing L1 = HR:** central walk-in corridor splitting Heads' offices (south) from the cubicle section (north), east exit stair. Both wings keep their **front stair shafts running L1→roof**.
- **Rear blocks:** centre column L1 = Cubical Hall (36 cubicles) opening to the lobby by two 4 m doorways; west rear = recruitment computer lab (5×10 networked seats facing a projector screen) + merged cubicles; east rear = 4 private head-of-department offices. **Stair towers at both rear outer corners** (L1→roof) with ground exits. Rear façade = solid wall with punched windows + curtains.
- **Wing upper floors (L2–8, both halves) = website pages** via raycastable `Floor_Tag_*` and `scene["zy_floors"]`: W2 Services, W3 Store, W4 Blog, W5 Work, W6 Projects (+`Room_Project_Tracking`), W7 HoD, W8 Directors; E2 Conference Centre, E3–E5 Departments A–C, E6 Operations, E7 Directors, **E8 Founders/CEO** boardroom.
- **Centre column floors 2–8 (`phase1_3_center_floors.py`):** the Phase-1.2 `Cubicle_Workspace_L1..L7` ring solids are retired and rebuilt as real open-plan cubicle floors — slab split around the vertical-core void so the glass lift and helix stairs run through, glazed bands north/south, **18 cubicles per floor** (126 total), and connections both ways: a core enclosure with a 3.2 m doorway onto the per-level `Lift_Door_*` lift lobby, plus west/east doorways at y 20–23 that line up with the rear-half inner-wall openings cut in `phase1_3_wing_floors.py`. Per-floor duct spine, diffusers and colour-coded tray.
- **Rooftop:** bulkhead room over each of the 4 staircases, helipad + detailed `Heli_*` helicopter, solar arrays on both wing roofs feeding `Solar_Plant_Room` (inverters + battery banks) with a riser into the building.
- **Site:** tile base + grout grid over the whole establishment (no bare grey), grassland on the **northern** slab (measured at runtime), turquoise walking-path ring, connected parking near the south fence with mixed `Car_Sedan_*`/`Car_SUV_*`, dual road linking the gates, east-fence gate.
- **Fence + guard (`phase1_3_gates_guard.py`):** the solid south fence is retired and rebuilt as segments with **real cutouts** — vehicle IN, vehicle OUT, pedestrian — each with piers, caps, header/sign, barred leaves, track, lamps. `Enternace_Area` is retired and rebuilt **hollow** as the true guard/entrance room: street + site doors, huge mullioned window bands, and all security **inside** (walk-through human scanner, bag X-ray with conveyors/trays/monitor, guard desk, queue barriers, benches) plus AC (4 ceiling cassettes, 2 split units, 3 roof condensers).
- **Scene props:** `zy_lobby`, `zy_west_wing`, `zy_east_wing`, `zy_rear`, `zy_floors`, `zy_roof`, `zy_site`, `zy_guard`. Palette ~30 `ZY_*`.

### Polish pass (`phase1_3_polish.py`, runs LAST, idempotent via a `zy_polished` stamp)
1,369 prop meshes beveled in place with bmesh (survives glTF export — no modifier stack); 200 chairs upgraded from bare cylinders to gas post + 5-star base + castors (kept rotationally symmetric on purpose — floors seat people facing different ways, so an oriented backrest would be wrong half the time); 215 desks/counters given legs + modesty panels; 3 couches given feet; 10 cars given bumpers, head/tail lights and mirrors oriented off each body's rotation; 38 `ZY_*` materials retuned with real roughness/metallic.

### Bug found and fixed while reframing a camera
The centre-floor lift enclosure originally opened **south** into a ~0.6 m dead end (the gap between the core wall and the floor's south perimeter). Nobody could have used it. The door now sits on the **east** face, opening onto the stair SE corner platform that leads to the lift landing.

---

## 9. Handover — product vision + next session

### 9.1 What this actually is (stated by the user 2026-07-18)
The site is a **mini EA-Sims-style experience**, not a scrolling page:
- The visitor **walks around the building** in first/third person and **talks to NPCs** to ask questions.
- **The lift IS the navigation bar.** The visitor steps into the glass lift, picks a destination, and the lift travels to that floor. Arriving on a floor = navigating to that page.
- **NPCs are the page content guides.** On arrival, that floor's NPC explains what the page offers.
- The **main portfolio repository's functionality is mapped onto the building floor by floor and room by room** — each existing feature/page becomes a physical place.

This reframes Phase 2: `CameraController` is a **character controller + lift UI**, not a scroll rig. The lift panel is the primary nav component; scroll-build (§3) is secondary or dropped.

### 9.2 Navigation map (already built into the model)
Floor ↔ page is carried in-scene by `scene["zy_floors"]` and raycastable `Floor_Tag_*` meshes, so the frontend can read it from the GLB rather than hard-coding:

| Lift stop | West wing | East wing |
|---|---|---|
| L1 | Waiting Room (visitor arrival) | HR Department |
| L2 | **Services** | Conference Center |
| L3 | **Store** | Departments A |
| L4 | **Blog** | Departments B |
| L5 | **Work** | Departments C |
| L6 | **Projects** (+ `Room_Project_Tracking`) | Operations |
| L7 | HoD Offices | Directors |
| L8 | Directors West | **Founders / CEO** |

Also: **Grand Lobby = About page** (`Lobby_Display_About_1..6` + `Lobby_Display_Hero`), **centre column L1** = Cubical Hall, **centre L2–8** = open workspace floors, **basement** = gym/pool + cafeteria, **guard room** = login/signup/guest entry.

### 9.3 NPC roster (23, all raycastable, props survive glTF)
Props on every NPC: `npc_id`, `npc_type`, `npc_role`, `npc_page`.
- `NPC_Lobby_Greeter` — deterministic, lobby/About.
- `NPC_Gate_Auth` — deterministic, guard room → drives login / signup / guest.
- 14 wing page-floor guides — **generative** for content pages (Services, Store, Blog, Work, Projects, Founders_CEO), **deterministic** for corporate floors.
- 7 `NPC_Center_L2..L8` — deterministic workspace supervisors.
Per §4: deterministic → hardcoded React decision tree; generative → `POST /api/chat` → RAG backend.

### 9.4 Execution contract (unchanged, and non-negotiable)
Everything in §7 still applies. Two failure modes cost real time this session:
- **The port-5000 listener can die** (socket closed → connection refused). Only the user can re-arm it inside Blender. The port-9876 MCP addon is not a fallback — it accepts TCP but its requests time out.
- **Timers only fire when Blender's event loop ticks.** If the user isn't hovering the viewport, scripts POST fine but never execute and no status JSON appears. "No status" almost always means idle viewport, not a broken script.
- Scratchpad path is session-specific — resolve it by listing `…/Temp/claude/C--Users-alira-Documents-portfolio-3d/*/scratchpad` and taking the one with recent files. Do not assume.
- Saving: `bpy.ops.wm.save_mainfile()` from a timer works, but the status JSON often fails to flush. **Verify saves by the .blend's `LastWriteTime`, not by the JSON.**

### 9.5 Known gaps (honest state)
- **Surfaces: partly addressed 2026-07-19 (`phase1_3_materials.py`).** All 36 `ZY_*` materials are now **procedural node graphs** — noise / wave / brick driving base-colour variation, roughness variation and bump, via the `Generated` coordinate input (no unwrap or image files needed). **9,782 meshes** also received a box-projected `ZY_UV` layer.
- **⚠ CRITICAL CAVEAT: glTF does not carry procedural nodes.** Those materials improve **Blender renders only**. The GLB that Phase 2 consumes will still be flat until they are **baked to image textures**. Do not assume the web build inherits this.
- **`ZY_UV` is box-projected and OVERLAPS.** Correct for tiling, unusable for a lightmap. A bake needs a second, non-overlapping `ZY_BAKE` set (smart-project per merged mesh).
- **No baked lighting.** Reference-quality browser 3D bakes lighting into textures; ours is real-time flat lighting. Nothing is baked yet.
- **No emissive/atmosphere pass** — no lit signage, glowing screens, fog, or dusk/night grading.
- **Scope reality:** the reference is a ~20×20 m diorama with locked cameras; this is a ~150×190 m campus with 8 occupiable floors and ~7,000 objects. Uniform fidelity at that level is months of art work. The realistic play is to **constrain what the camera ever sees, then detail only that** (lobby, entrance approach, one office floor, rooftop) and leave the rest as background massing.
- **GLB export not started.** ~7,000 separately-material'd objects will export heavy and still look flat. Baking + joining per area into atlased textures is both a quality and a performance win, and should happen **before** Phase 2.

### 9.6 Next steps (in recommended order)
1. ~~Procedural node materials~~ **DONE 2026-07-19.** Still outstanding from this step: **emissive signage/screens + dusk/night atmosphere** — darkness flatters untextured geometry and lets emissives carry the scene.
2. **Bake to images — the real unlock, and now the top priority.** In order: (a) **join meshes per zone** (lobby / each floor / site / roof) — ~9,800 objects is both a bake problem and a GLB size problem; (b) smart-project a **non-overlapping `ZY_BAKE` UV set** per merged mesh; (c) **bake diffuse + AO in Cycles** to per-zone atlases; (d) rewire materials to those images. Only after this does the GLB actually look like the Blender renders.
3. **Prop density in hero areas only.**
4. **Phase 1.5 export** → `zyvion_hq.glb` into the web project's `/public/models/`.
5. **Phase 2 (R3F)** — character controller + **lift navigation UI** + NPC raycast/chat overlay, reading the floor↔page map from the GLB.

**Do not start Phase 2 until the user confirms.**