/* =============================================================================
   Résumé data — the single source of truth for the downloadable CV, transcribed
   faithfully from the repo-root `cv-reference.md` (the user's golden file). Every
   claim here is grounded in real CodeWatch / NETSOL work. DO NOT fabricate jobs,
   metrics, or skills, and don't reintroduce the student email or semester counts
   (see cv-reference.md §8 style guidelines).
   ========================================================================== */

export interface SkillGroup {
  label: string;
  items: string[];
}
export interface ResumeRole {
  title: string;
  org: string;
  meta: string; // dates · location/role
  stack?: string;
  bullets: string[];
  link?: string;
  linkLabel?: string;
}
export interface ResumeData {
  name: string;
  title: string;
  location: string;
  email: string;
  phone: string;
  github: string; // display label
  githubUrl: string;
  linkedinLabel: string; // long slug → clean "LinkedIn" label per cv-reference
  linkedinUrl: string;
  website: string; // the portfolio site — the CV's call-to-action
  websiteLabel: string;
  flagshipProjectId: string; // which personalProjects entry is the detailed flagship
  summary: string;
  strengths: string[];
  skills: SkillGroup[];
  flagship: ResumeRole;
  experience: ResumeRole[];
  education: {
    degree: string;
    school: string;
    meta: string;
    coursework: string[];
  };
}

export const RESUME: ResumeData = {
  name: "Muhammad Ali Raza",
  title: "Computer Vision & Full-Stack AI Engineer",
  location: "Lahore, Pakistan",
  email: "shahjee975@gmail.com",
  phone: "+92 341 4527256",
  github: "github.com/SMARNB",
  githubUrl: "https://github.com/SMARNB",
  linkedinLabel: "LinkedIn",
  linkedinUrl: "https://www.linkedin.com/in/muhammad-ali-r-43713598/",
  website: "https://smarnb.onrender.com",
  websiteLabel: "smarnb.onrender.com",
  flagshipProjectId: "codewatch",

  summary:
    "Computer Science graduate specializing in real-time computer vision and full-stack " +
    "engineering. Designed and built CodeWatch, a multi-camera surveillance platform that " +
    "detects, tracks, and identifies people across live video feeds and enforces access rules " +
    "in real time. Comfortable across the whole stack — from GPU inference pipelines and model " +
    "fine-tuning to REST APIs and production React dashboards — with a focus on shipping " +
    "working, end-to-end systems.",

  // Defensible positioning tags drawn straight from the skills + flagship project.
  strengths: [
    "Real-time computer vision",
    "Full-stack engineering",
    "Model fine-tuning",
    "Multithreaded pipelines",
    "REST API design",
    "Production React dashboards",
  ],

  skills: [
    { label: "Languages", items: ["Python", "JavaScript", "C++", "SQL"] },
    {
      label: "Computer Vision & ML",
      items: [
        "YOLOv11 / YOLO26 (Ultralytics)",
        "InsightFace",
        "DeepSort",
        "OpenCV",
        "PyTorch (CUDA)",
        "TensorFlow / Keras",
        "ONNX Runtime",
        "scikit-learn",
        "NumPy",
        "pandas",
      ],
    },
    {
      label: "ML techniques",
      items: [
        "Transfer learning & fine-tuning",
        "Dataset augmentation",
        "Vector embeddings",
        "Cosine-similarity search",
        "Anti-spoofing (PAD)",
      ],
    },
    {
      label: "Backend",
      items: [
        "Django",
        "Django REST Framework",
        "PostgreSQL",
        "Redis",
        "Flask",
        "Gunicorn",
        "Multithreading",
        "REST API design",
      ],
    },
    {
      label: "Frontend",
      items: ["React 19", "Vite", "Tailwind CSS", "Chart.js / Recharts", "Axios", "React Router"],
    },
    {
      label: "Tooling & delivery",
      items: ["Git", "PyInstaller", "MediaMTX (RTSP)", "Selenium", "Postman", "Figma", "Linux / Windows"],
    },
  ],

  flagship: {
    title: "CodeWatch — Real-Time Multi-Camera Surveillance & Access Control",
    org: "Final Year Project",
    meta: "2025 – 2026 · Architecture & full-stack development",
    stack: "Python · PyTorch · Django REST · React · Redis · PostgreSQL · OpenCV",
    link: "https://github.com/SMARNB/CodeWatch",
    linkLabel: "github.com/SMARNB/CodeWatch",
    bullets: [
      "Built an end-to-end pipeline that ingests live RTSP/MJPEG feeds and, per frame, detects " +
        "people (YOLO26/YOLO11 segmentation), tracks them (DeepSort), and identifies them against " +
        "a face database (InsightFace 512-d embeddings, vectorized cosine matching).",
      "Engineered a multithreaded engine (one thread per camera, shared model singletons guarded " +
        "by locks) sustaining the full detect → track → identify → dress-code pipeline at ~5 " +
        "analyzed FPS, scaling to ~8 cameras per GPU.",
      "Fine-tuned a custom YOLO dress-code detector (15 clothing categories) via two-stage " +
        "transfer learning with a frozen backbone, plus a data-augmentation pipeline to re-label " +
        "samples and close class gaps.",
      "Added a MiniFASNet anti-spoofing (presentation-attack-detection) module in TorchScript, " +
        "benchmarked at ~3.6 ms/face, to reject photo and replay spoofs before identity matching.",
      "Implemented cross-camera identity hand-off with Redis TTL keys, auto-blacklisting via DB " +
        "signals, and deduped violation logging.",
      "Designed the Django REST backend (PostgreSQL, Redis, role-based access, email/push " +
        "notifications) and a React 19 + Tailwind operator dashboard with live feeds, analytics, " +
        "movement heatmaps, and PDF reports.",
      "Packaged the full stack (CV engine, API, dashboard, RTSP server) into a one-click " +
        "system-tray desktop launcher (PyInstaller / PyQt5) for non-technical operators.",
    ],
  },

  experience: [
    {
      title: "Generative AI Intern",
      org: "NETSOL Technologies",
      meta: "Lahore · 2024",
      bullets: [
        "Built Selenium automation for large-scale web data scraping and extraction.",
        "Developed data-preprocessing pipelines — document chunking and OCR — to digitize source " +
          "material for model training.",
        "Generated and managed vector embeddings to support training and retrieval for custom AI models.",
      ],
    },
  ],

  education: {
    degree: "BS Computer Science",
    school: "Riphah International University, Lahore, Pakistan",
    meta: "2021 – 2026",
    coursework: [
      "Artificial Intelligence",
      "Computer Vision",
      "Data Structures & Algorithms",
      "Database Systems",
      "Web Engineering",
      "Object-Oriented Programming",
      "System Architecture",
    ],
  },
};
