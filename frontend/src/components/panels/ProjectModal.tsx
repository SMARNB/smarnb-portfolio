/* Portfolio project detail modal — opened from the "Selected work" cards. Shows
   the project art/details and a CTA that seeds the contact form and scrolls to
   it. Port of openProject() in app.js. */
import { useNavigate } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { MediaFrame, kindFor } from "../../lib/art";
import { portfolio } from "../../lib/data";
import { setContactPrefill } from "../../lib/contactPrefill";
import { useUI } from "../../context/UIContext";

export function ProjectModal() {
  const { isOpen, close, stack } = useUI();
  const navigate = useNavigate();
  const open = isOpen("project");
  const panel = stack.find((p) => p.type === "project") as { type: "project"; id: string } | undefined;
  const p = panel ? portfolio.find((x) => x.id === panel.id) : undefined;

  function startSimilar() {
    if (p) setContactPrefill(`I'm interested in a project similar to “${p.title}”. `);
    close("project");
    navigate("/contact");
  }

  return (
    <div
      className={`modal${open ? " open" : ""}`}
      id="projectModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="projectTitle"
      aria-hidden={!open}
    >
      <div className="modal-head">
        <h3 id="projectTitle">{p ? p.title : "Project"}</h3>
        <button className="close-btn" aria-label="Close project" onClick={() => close("project")}>
          <Icon name="close" size={20} />
        </button>
      </div>
      <div className="modal-body" id="projectBody">
        {p && (
          <>
            <MediaFrame
              kind={kindFor(p.category)}
              className="modal-media"
            />
            <span
              className="cat"
              style={{
                display: "inline-block",
                marginTop: "1rem",
                color: "var(--muted-2)",
                fontWeight: 700,
                textTransform: "uppercase",
                fontSize: ".76rem",
                letterSpacing: ".08em",
              }}
            >
              {p.category}
            </span>
            <h3 style={{ margin: ".3rem 0 .5rem" }}>{p.title}</h3>
            <p className="lead">{p.desc}</p>
            <div className="tag-row" style={{ margin: "1rem 0 1.4rem" }}>
              {p.tags.map((t) => (
                <span className="tag" key={t}>{t}</span>
              ))}
            </div>
            <button className="btn btn-primary btn-block" onClick={startSimilar}>
              <Icon name="spark" size={18} /> Start a similar project
            </button>
          </>
        )}
      </div>
    </div>
  );
}
