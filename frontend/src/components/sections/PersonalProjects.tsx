/* Personal & open-source projects — a featured card (CodeWatch) plus a grid of
   the rest. Port of renderPersonalProjects in app.js. */
import { Link } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { gradFor } from "../../lib/art";
import { personalProjects } from "../../lib/data";
import { Reveal } from "../ui/Reveal";

export function PersonalProjects() {
  const feat = personalProjects.filter((p) => p.featured);
  const rest = personalProjects.filter((p) => !p.featured);

  return (
    <section id="projects">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Personal &amp; open-source</span>
          <h2 className="section-title">Projects I've built</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            Things I've designed and engineered beyond client work — including my flagship computer-vision system,
            CodeWatch.
          </p>
        </Reveal>

        {feat.map((p) => (
          <Reveal className="card project-feature" key={p.id} as="article">
            <div
              className={`pf-visual${p.image ? " has-shot" : ""}`}
              style={p.image ? undefined : { background: gradFor(p.category) }}
            >
              {p.image ? (
                <>
                  <img className="pf-shot" src={p.image} alt={`${p.title} — ${p.subtitle}`} loading="lazy" />
                  <span className="pf-scrim" />
                  {p.logo && (
                    <span className="pf-logo">
                      <img src={p.logo} alt="" />
                    </span>
                  )}
                  <span className="pf-cat">{p.category}</span>
                  <span className="pf-name">{p.title}</span>
                </>
              ) : (
                <>
                  <Icon name="eye" className="pf-bigicon" />
                  <span className="pf-cat">{p.category}</span>
                  <span className="pf-name">{p.title}</span>
                </>
              )}
            </div>
            <div className="pf-body">
              <span className="eyebrow">Featured project</span>
              <h3>
                {p.title} <span className="pf-sub">— {p.subtitle}</span>
              </h3>
              <p className="pf-meta">{p.role} · {p.period}</p>
              <p className="lead">{p.desc}</p>
              <ul className="feat-list">
                {p.highlights.map((h) => (
                  <li key={h}>
                    <Icon name="check" /> <span>{h}</span>
                  </li>
                ))}
              </ul>
              <div className="tag-row">
                {p.tags.map((t) => (
                  <span className="tag" key={t}>{t}</span>
                ))}
              </div>
              <div className="hero-cta mt-4">
                <a className="btn btn-primary" href={p.link} target="_blank" rel="noopener">
                  <Icon name="github" size={18} /> {p.linkLabel || "View project"}
                </a>
                {p.licenseLink && (
                  <Link className="btn btn-outline" to={p.licenseLink}>
                    <Icon name="cart" size={18} /> {p.licenseLabel || "License this product"}
                  </Link>
                )}
              </div>
            </div>
          </Reveal>
        ))}

        {rest.length > 0 && (
          <div className="grid cols-2" style={{ marginTop: "1.25rem" }}>
            {rest.map((p) => (
              <Reveal className="card" key={p.id} as="article">
                <span className="cat" style={{ color: "var(--accent-2)", fontWeight: 700, textTransform: "uppercase", fontSize: ".74rem", letterSpacing: ".06em" }}>
                  {p.category}
                </span>
                <h3 style={{ fontSize: "1.15rem", margin: ".35rem 0" }}>{p.title}</h3>
                <p style={{ color: "var(--muted)", fontSize: ".93rem" }}>{p.desc}</p>
                <div className="tag-row">
                  {p.tags.map((t) => (
                    <span className="tag" key={t}>{t}</span>
                  ))}
                </div>
                <a className="card-link" href={p.link} target="_blank" rel="noopener">
                  {p.linkLabel || "View"} <Icon name="arrow" size={16} />
                </a>
              </Reveal>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
