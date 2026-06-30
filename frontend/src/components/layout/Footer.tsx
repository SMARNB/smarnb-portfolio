/* Footer — brand, config-driven social icons (dimmed placeholder when a link is
   not configured), services list (routes to the store), explore + contact links. */
import { Link } from "react-router-dom";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { shortTitle } from "../../lib/format";
import { useCatalog } from "../../context/CatalogContext";
import { useUI } from "../../context/UIContext";

const SOCIALS: { key: string; label: string }[] = [
  { key: "instagram", label: "Instagram" },
  { key: "facebook", label: "Facebook" },
  { key: "linkedin", label: "LinkedIn" },
  { key: "x", label: "X (Twitter)" },
  { key: "github", label: "GitHub" },
];

export function Footer() {
  const { services } = useCatalog();
  const { openTrack } = useUI();
  const wa = (CONFIG.whatsapp || "").replace(/\D/g, "");

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <Link className="brand" to="/">
              <span className="mark">{CONFIG.initials}</span>
              <span>{CONFIG.brand}</span>
            </Link>
            <p className="desc">{CONFIG.tagline}</p>
            <div className="socials">
              {SOCIALS.map(({ key, label }) => {
                const url = CONFIG.socials[key];
                return url ? (
                  <a key={key} href={url} target="_blank" rel="noopener" aria-label={label}>
                    <Icon name={key} size={18} />
                  </a>
                ) : (
                  /* Not configured yet: a decorative placeholder, hidden from the
                     a11y tree (no destination → not a link; aria-disabled on a
                     non-interactive element is invalid and was flagged by Lighthouse). */
                  <span
                    key={key}
                    className="social-empty"
                    aria-hidden="true"
                    title={`Add your ${key} link in config`}
                  >
                    <Icon name={key} size={18} />
                  </span>
                );
              })}
            </div>
          </div>
          <div>
            <h4>Services</h4>
            <ul>
              {services.map((s) => (
                <li key={s.id}>
                  <Link to={`/store#svc-${s.id}`}>{shortTitle(s.title)}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Explore</h4>
            <ul>
              <li><Link to="/projects">Projects</Link></li>
              <li><Link to="/work">Work</Link></li>
              <li><Link to="/about">Experience</Link></li>
              <li><Link to="/about">About</Link></li>
              <li><Link to="/app">Client login</Link></li>
              <li>
                <a href="#" onClick={(e) => { e.preventDefault(); openTrack(); }}>
                  Track an order
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4>Get in touch</h4>
            <ul>
              <li><a href={`mailto:${CONFIG.email}`}>{CONFIG.email}</a></li>
              <li><a href={`https://wa.me/${wa}`} target="_blank" rel="noopener">WhatsApp</a></li>
              <li><Link to="/contact">Custom request</Link></li>
            </ul>
          </div>
        </div>
        <div className="foot-bottom">
          <span>© {new Date().getFullYear()} {CONFIG.name}. All rights reserved.</span>
          <span>Built for speed · accessibility · security</span>
        </div>
      </div>
    </footer>
  );
}
