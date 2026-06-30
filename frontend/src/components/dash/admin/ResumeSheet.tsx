/* The rendered A4 résumé — modern one-page, two-column, teal accent (#0d9488),
   deep-ink headings (#0f172a), Inter, pill "strengths" tags and inline SVG contact
   icons, matching the design language in cv-reference.md §8. Self-contained styling
   lives in dashboard.css (.resume-*), so this same markup renders identically in
   the on-screen preview and in the print-to-PDF output. */
import { RESUME } from "../../../lib/resume";

function I({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {/* d is a sequence of <path>/<circle> markup strings */}
      <g dangerouslySetInnerHTML={{ __html: d }} />
    </svg>
  );
}

const ICON = {
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  phone:
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z"/>',
  pin: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  github:
    '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>',
  linkedin:
    '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6Z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
};

export function ResumeSheet() {
  const r = RESUME;
  return (
    <div className="resume-sheet" id="resumeSheet">
      <header className="resume-head">
        <h1 className="resume-name">{r.name}</h1>
        <p className="resume-title">{r.title}</p>
        <div className="resume-contacts">
          <a href={`mailto:${r.email}`}><I d={ICON.mail} /> {r.email}</a>
          <span><I d={ICON.phone} /> {r.phone}</span>
          <span><I d={ICON.pin} /> {r.location}</span>
          <a href={r.githubUrl}><I d={ICON.github} /> {r.github}</a>
          <a href={r.linkedinUrl}><I d={ICON.linkedin} /> {r.linkedinLabel}</a>
        </div>
      </header>

      <div className="resume-body">
        {/* Main column */}
        <main className="resume-main">
          <section className="resume-block">
            <h2 className="resume-h2">Profile</h2>
            <p className="resume-summary">{r.summary}</p>
          </section>

          <section className="resume-block">
            <h2 className="resume-h2">Flagship Project</h2>
            <div className="resume-role">
              <div className="resume-role-head">
                <h3 className="resume-role-title">{r.flagship.title}</h3>
                <span className="resume-role-meta">{r.flagship.meta}</span>
              </div>
              <p className="resume-role-org">{r.flagship.org}</p>
              {r.flagship.stack && <p className="resume-stack">{r.flagship.stack}</p>}
              <ul className="resume-bullets">
                {r.flagship.bullets.map((b, i) => <li key={i}>{b}</li>)}
              </ul>
            </div>
          </section>

          <section className="resume-block">
            <h2 className="resume-h2">Experience</h2>
            {r.experience.map((e, i) => (
              <div className="resume-role" key={i}>
                <div className="resume-role-head">
                  <h3 className="resume-role-title">{e.title}</h3>
                  <span className="resume-role-meta">{e.meta}</span>
                </div>
                <p className="resume-role-org">{e.org}</p>
                <ul className="resume-bullets">
                  {e.bullets.map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              </div>
            ))}
          </section>
        </main>

        {/* Sidebar */}
        <aside className="resume-side">
          <section className="resume-block">
            <h2 className="resume-h2">Strengths</h2>
            <div className="resume-pills">
              {r.strengths.map((s) => <span className="resume-pill" key={s}>{s}</span>)}
            </div>
          </section>

          <section className="resume-block">
            <h2 className="resume-h2">Technical Skills</h2>
            {r.skills.map((g) => (
              <div className="resume-skill" key={g.label}>
                <p className="resume-skill-label">{g.label}</p>
                <p className="resume-skill-items">{g.items.join(" · ")}</p>
              </div>
            ))}
          </section>

          <section className="resume-block">
            <h2 className="resume-h2">Education</h2>
            <div className="resume-edu">
              <h3 className="resume-role-title">{r.education.degree}</h3>
              <p className="resume-role-org">{r.education.school}</p>
              <span className="resume-role-meta">{r.education.meta}</span>
              <p className="resume-skill-items resume-course">
                {r.education.coursework.join(" · ")}
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
