/* Home-page section teaser header: eyebrow + title on the left, a "See all →"
   link to the full page on the right. Used by the Work / Projects / Blog home
   previews (each shows at most 3 cards). */
import { Link } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { Reveal } from "./Reveal";

export function TeaserHead({
  eyebrow,
  title,
  to,
  label,
}: {
  eyebrow: string;
  title: string;
  to: string;
  label: string;
}) {
  return (
    <Reveal className="teaser-head">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2 className="section-title">{title}</h2>
      </div>
      <Link className="teaser-all" to={to}>
        {label} <Icon name="arrow" size={16} />
      </Link>
    </Reveal>
  );
}
