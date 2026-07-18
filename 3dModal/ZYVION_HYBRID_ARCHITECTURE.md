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

### Known open items
- Older box assets (desks, cars, cubicles, couches) still read as low-detail; only the gate/security work has bevels + metallic materials so far.
- The guard-room interior preview camera is mis-framed (sits on the desk monitors); the room itself is correct.

### Next step
Phase 1.4 (roof/exterior polish) and Phase 2 (R3F frontend) — **do not start until the user confirms**.