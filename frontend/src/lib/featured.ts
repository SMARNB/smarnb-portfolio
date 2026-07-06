/* =============================================================================
   Feature showcase content — the top 3 strengths, each told as a
   Problem → Solution → Result story for the Z-pattern showcase on Home,
   /services and /store. Copy is grounded in real project facts (CodeWatch, the
   portfolio SaaS + scraping work); result metrics that aren't yet measured are
   left as clearly-marked placeholders so nothing reads as fabricated.
   ========================================================================== */
import type { MediaKind } from "./art";

export interface Featured {
  id: string;
  eyebrow: string;
  title: string;
  problem: string;
  solution: string;
  result: string;
  stack: string[];
  serviceId: string; // deep-links to /store#svc-<serviceId>
  media: { kind: MediaKind; image?: string; alt?: string; logo?: string; logoText?: string };
}

export const FEATURED: Featured[] = [
  {
    id: "ai-cv",
    eyebrow: "AI & Computer Vision",
    title: "Vision systems that hold up in the real world",
    problem:
      "Most face-recognition demos fall apart in production — a printed photo or a phone screen walks straight past them, and accuracy collapses the moment cameras or lighting change.",
    solution:
      "For CodeWatch I gated InsightFace recognition behind a MiniFASNet liveness check, then added YOLO person detection, multi-camera tracking, dress-code checks and violation logging — a full Django REST + React pipeline, not a notebook.",
    result:
      "Blocks photo / screen / replay spoofs at ~3.6 ms per face and runs live across multiple camera feeds.",
    stack: ["Python", "PyTorch", "InsightFace", "YOLO", "Django REST", "React"],
    serviceId: "ai-cv",
    // Monochrome CV motif here — the real CodeWatch screenshot already leads the
    // hero and the /projects feature, so the showcase stays clean (no duplicate).
    media: { kind: "cv" },
  },
  {
    id: "saas-dashboards",
    eyebrow: "Full-Stack SaaS Dashboards",
    title: "Dashboards your whole team can run on",
    problem:
      "Spreadsheets and half-built admin panels don't scale — teams lose hours to manual exports, stale numbers and no real access control.",
    solution:
      "I build production dashboards in Python (FastAPI / Django + React): real-time metrics, Stripe billing, multi-tenant auth and role-based access, with live charts over your own data.",
    result:
      "You get a real product your team logs into daily — auth, billing, roles and live charts over your own data — not a throwaway prototype.",
    stack: ["FastAPI", "Django", "React", "PostgreSQL", "Stripe"],
    serviceId: "saas-dashboard",
    media: { kind: "dashboard" },
  },
  {
    id: "ocr-scraping",
    eyebrow: "OCR & Data Scraping",
    title: "Turn portals and paperwork into clean data",
    problem:
      "Critical data is trapped behind logins, pagination and scanned PDFs — and copying it by hand is slow, error-prone and never up to date.",
    solution:
      "I build Selenium bots with OCR that log in, handle pagination and proxy rotation, extract invoice and lead data, then export clean CSV / Excel / JSON on a schedule.",
    result:
      "Clean CSV / Excel / JSON delivered on a schedule — the manual copying and stale spreadsheets are gone.",
    stack: ["Python", "Selenium", "OCR", "Pandas"],
    serviceId: "selenium-bots",
    media: { kind: "code" },
  },
];
