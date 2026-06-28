/* FAQ accordion — single open item, animated via the CSS grid-rows trick. Port of
   renderFAQ in app.js. */
import { useState } from "react";
import { Icon } from "../../lib/icons";
import { faq } from "../../lib/data";
import { Reveal } from "../ui/Reveal";

export function Faq() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Questions</span>
          <h2 className="section-title">Frequently asked</h2>
        </Reveal>
        <div className="faq" id="faqList">
          {faq.map((f, i) => {
            const isOpen = open === i;
            return (
              <div className={`faq-item${isOpen ? " open" : ""}`} key={i}>
                <button
                  className="faq-q"
                  aria-expanded={isOpen}
                  aria-controls={`faq-a-${i}`}
                  onClick={() => setOpen(isOpen ? null : i)}
                >
                  <span>{f.q}</span>
                  <Icon name="chevron" className="chev" size={22} />
                </button>
                <div className="faq-a" id={`faq-a-${i}`} role="region">
                  <div>
                    <p>{f.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
