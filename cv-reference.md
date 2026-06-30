# Muhammad Ali Raza — CV Reference / Source of Truth

> **Purpose:** A portable, plain-text reference for any chat session or tool that needs to
> work with this CV — tailoring it to a job, writing a cover letter, drafting LinkedIn/bio
> copy, or prepping for interviews — **without re-deriving the facts from the codebase**.
>
> **Rendered CV lives at:** `C:\Users\alira\Downloads\Muhammad_Ali_Raza_CV.pdf` (one page) and
> `…\Muhammad_Ali_Raza_CV.html` (editable source; render to PDF with headless Chrome).
> **Last updated:** 2026-06-30.
>
> **Golden rule:** every claim here is grounded in real work on the CodeWatch project. **Do not
> fabricate** jobs, metrics, or skills. If you enrich, pull from the "Ground-truth technical
> facts" section below, which is taken from the project's own docs.

---

## 1. Identity & Contact (confirmed)

| Field | Value |
|---|---|
| Name (CV display) | **Muhammad Ali Raza** (full/legal: Syed Muhammad Ali Raza Naqvi Bukhari) |
| Title / positioning | **Computer Vision & Full-Stack AI Engineer** |
| Email | **shahjee975@gmail.com** *(personal — chosen over the expiring student email)* |
| Phone | **+92 341 4527256** |
| Location | Lahore, Pakistan |
| GitHub | **github.com/SMARNB** — https://github.com/SMARNB |
| LinkedIn | https://www.linkedin.com/in/syed-muhammad-ali-raza-naqvi-bukhari-311599412/ |

> **Contact display notes:** the LinkedIn slug is very long, so the CV shows a clean clickable
> "LinkedIn" label rather than the raw URL. Recommend setting a LinkedIn vanity URL
> (e.g. `linkedin.com/in/smarnb`) so a readable handle can be shown.

---

## 2. Professional Summary

> Computer Science graduate specializing in **real-time computer vision** and **full-stack
> engineering**. Designed and built **CodeWatch**, a multi-camera surveillance platform that
> detects, tracks, and identifies people across live video feeds and enforces access rules in
> real time. Comfortable across the whole stack — from GPU inference pipelines and model
> fine-tuning to REST APIs and production React dashboards — with a focus on shipping working,
> end-to-end systems.

---

## 3. Technical Skills (grouped, all real)

- **Languages:** Python, JavaScript, C++, SQL
- **Computer Vision & ML:** YOLOv11 / YOLO26 (Ultralytics), InsightFace, DeepSort, OpenCV,
  PyTorch (CUDA), TensorFlow / Keras, ONNX Runtime, scikit-learn, NumPy, pandas
- **ML techniques:** transfer learning & model fine-tuning, dataset augmentation, vector
  embeddings, cosine-similarity search, anti-spoofing (PAD)
- **Backend:** Django, Django REST Framework, PostgreSQL, Redis, Flask, Gunicorn,
  multithreading, REST API design
- **Frontend:** React 19, Vite, Tailwind CSS, Chart.js / Recharts, Axios, React Router
- **Tooling & delivery:** Git, PyInstaller, MediaMTX (RTSP), Selenium, Postman, Figma,
  Linux / Windows

> **Do NOT claim:** pgvector as the matching engine (it's installed but matching is done in
> NumPy/cosine in-process), Docker, Kubernetes, or any cloud platform — none are used here.

---

## 4. Flagship Project — CodeWatch

**CodeWatch — Real-Time Multi-Camera Surveillance & Access Control**
Final Year Project · 2025 – 2026 · Architecture & full-stack development
*Stack: Python, PyTorch, Django REST, React, Redis, PostgreSQL, OpenCV*

**Polished CV bullets (as they appear on the CV):**

- Built an end-to-end pipeline that ingests live RTSP/MJPEG feeds and, per frame, detects people
  (YOLO26/YOLO11 segmentation), tracks them (DeepSort), and identifies them against a face
  database (InsightFace 512-d embeddings with vectorized cosine matching).
- Engineered a multithreaded engine (one thread per camera, shared model singletons guarded by
  locks) sustaining the full detect → track → identify → dress-code pipeline at ~5 analyzed FPS,
  scaling to ~8 cameras per GPU.
- Fine-tuned a custom YOLO dress-code detector (15 clothing categories) via two-stage transfer
  learning with a frozen backbone, plus a data-augmentation pipeline to extract and re-label
  samples and close class gaps.
- Added a MiniFASNet anti-spoofing (presentation-attack-detection) module in TorchScript,
  benchmarked at ~3.6 ms/face, to reject photo and replay spoofs before identity matching.
- Implemented cross-camera identity hand-off with Redis TTL keys so a person retains one identity
  while moving between cameras; added auto-blacklisting via DB signals and deduped violation logging.
- Designed the Django REST backend (PostgreSQL, Redis cache, role-based access, email/push
  notifications) and a React 19 + Tailwind operator dashboard with live feeds, analytics,
  movement heatmaps, and PDF reports.
- Packaged the full stack (CV engine, API, dashboard, RTSP server) into a one-click system-tray
  desktop launcher (PyInstaller / PyQt5) for non-technical operators.

### Ground-truth technical facts (for cover letters / interview prep — all defensible)

- **What it is:** a real-time, multi-camera surveillance system for a university campus. Watches
  RTSP/MJPEG feeds, detects every person, identifies them against a face DB, checks dress-code
  compliance, and logs violations. Three alert types: **Dress Code Violation**, **Unauthorized
  Access**, **Blacklisted Person Detected** — each writes to the DB, fires a notification, and can
  email the person.
- **Model stack:** YOLO26n-seg (primary) / YOLO11n-seg (fallback) for person detection +
  segmentation; a custom-trained dress-code YOLO detector; **InsightFace buffalo_l** (CUDA,
  det_size 640×640) for **512-d** face embeddings; **DeepSort** (MobileNetV2 re-ID) for tracking.
- **Concurrency model:** single Python process; a `WatcherThread` polls Django every 30 s for
  cameras/registry/blacklist and spawns one `CameraThread` per active camera; each camera thread
  owns its own YOLO instance; the shared InsightFace model + registry are guarded by
  `threading.Lock`s. Fire-and-forget daemon threads do non-blocking API POSTs.
- **Matching:** vectorized cosine similarity (NumPy dot product over a flattened embedding matrix);
  threshold **0.50**; named persons preferred over auto-registered unknowns.
- **Redis usage:** `global_identity:{id}` (TTL 30 s) for cross-camera identity hand-off;
  `track_highlight` to spotlight a person from the UI; rate-limit + counter keys for unknown
  registration.
- **Dress-code logic:** model class names prefixed `m-`/`w-` infer gender by majority vote;
  violation rule-sets per gender; 30 s per-(camera,track) cooldown to avoid alert spam. Trained in
  two stages (base, then `freeze=10` for ~50 epochs, batch 16). Dataset augmented by extracting and
  re-labeling sleeveless samples and merging with an 80/15/5 split.
- **Auto-blacklist:** a Django `post_save` signal counts a person's violations; at 10 it auto-creates
  a Blacklist entry and flips classification to `blacklisted`; the live engine picks it up within ~60 s.
- **Liveness/PAD:** single **MiniFASNetV2** in TorchScript (`trace` + `optimize_for_inference`),
  measured **~3.6 ms/face** forward pass over n=300 (`perf_counter`); InsightFace recognition is
  ~25–30 ms/face.
- **Scaling anchor:** ~8 cameras per consumer GPU (4090-class) at ~5 analyzed FPS, full pipeline;
  data-center GPUs + TensorRT → ~20–30 per GPU. In-process threaded engine tops out ~10–20 cameras
  before it must be sharded.
- **Frontend delivery:** the engine writes annotated `live_feed_{camera_id}.jpg` frames that the
  React dashboard polls (~300 ms) — no WebSocket/RTSP to the browser. Dashboard has role-based
  layouts (admin vs guard), person registry, analytics (Chart.js/Recharts), movement heatmaps,
  notification bell, and client-side PDF report export (jsPDF).
- **Packaging:** one-click launcher boots MediaMTX + Django + Vite (HTTPS) + the CV engine, runs in
  the system tray (pystray/PyQt5), no terminal window.

> **Honest limits (state these if asked — they signal maturity, not weakness):** accuracy depends
> on camera angle/lighting; gender for dress-code is a clothing heuristic, not a classifier; dense
> crowds raise tracking ID-switches; biometric data isn't yet encrypted at rest; the anti-spoofing
> module is validated on the public Silent-Face samples (not yet calibrated on our own cameras) and
> fail-opens on faces too small/distant to score.

---

## 5. Experience — NETSOL Technologies

**Generative AI Intern** · NETSOL Technologies, Lahore · *2024 (year unconfirmed — verify)*

- Built Selenium automation for large-scale web data scraping and extraction.
- Developed data-preprocessing pipelines — document chunking and OCR — to digitize source material
  for model training.
- Generated and managed vector embeddings to support training and retrieval for custom AI models.

---

## 6. Education & Coursework

**BS Computer Science** — Riphah International University, Lahore, Pakistan · **2021 – 2026**

Relevant coursework: Artificial Intelligence · Computer Vision · Data Structures & Algorithms ·
Database Systems · Web Engineering · Object-Oriented Programming · System Architecture

> The degree spanned ~11 semesters; this is intentionally absorbed into the **2021 – 2026** range
> and **never called out**. Do not add semester counts or explain the duration on the CV.

---

## 7. Confirmed vs. Assumed (verify before sending)

| Item | Status |
|---|---|
| Name, email, phone, GitHub, LinkedIn | ✅ Confirmed by user |
| Education dates 2021 – 2026 | ✅ Confirmed (started 2021, graduated 2026) |
| CodeWatch FYP 2025 – 2026 | ⚠️ Inferred as the final year — reasonable, confirm |
| NETSOL internship year (2024) | ⚠️ **Assumed** — get the real date |
| FYP role ("Architecture & full-stack development") | ⚠️ Team size unknown — only claim "sole developer" if it was solo |

---

## 8. Style & claim guidelines (for any session editing this CV)

- **Keep every claim interview-defensible.** Prefer specific, real numbers (512-d embeddings,
  ~3.6 ms/face, ~8 cameras/GPU, 15 dress classes) over vague superlatives. Don't invent accuracy
  percentages — none were formally benchmarked.
- **Don't reintroduce** the student email (`38672@students.riphah.edu.pk`) or the 11-semester detail.
- **Design language of the rendered CV:** modern one-page, two-column; teal accent (`#0d9488`),
  deep-ink headings (`#0f172a`); Inter font (Segoe UI fallback); pill "strengths" tags; inline SVG
  contact icons. A4, ~one page.
- **Rendering:** edit the `.html`, then headless Chrome `--print-to-pdf`. On this machine Chrome
  can't write to Downloads/Documents (Controlled Folder Access) — render to `%TEMP%` then copy.
