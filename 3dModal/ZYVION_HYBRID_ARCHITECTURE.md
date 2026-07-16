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