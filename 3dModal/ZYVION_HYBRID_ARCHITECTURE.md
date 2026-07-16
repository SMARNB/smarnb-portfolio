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

### Next step
Phase 1.3 begins with the **Grand Lobby interior** — it doubles as the portfolio About page (graphics/displays) and hosts the Lobby Greeter NPC. The lobby is currently a SOLID 50×50×24.4 box (`Grand_Lobby_4_Story` at (0, −25), z 9.23–33.63) that must be hollowed (shell + entry from the front entrance stairs) before furnishing.