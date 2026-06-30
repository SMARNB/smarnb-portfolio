/* Admin "Résumé" tab — renders the one-page CV (from cv-reference data) exactly as
   it should print, with a live preview and a one-click "Download PDF" that uses the
   browser's native print-to-PDF.

   Why print-to-PDF (not server-side headless Chrome): it's 100% first-party, needs
   no extra server dependency (Render's box has no Chrome), and sidesteps the
   Controlled-Folder-Access gotcha — the browser's own "Save as PDF" lets the user
   pick any location. The résumé is rendered a SECOND time through a portal attached
   straight to <body>, so on print we hide #root and show only that copy — the
   dashboard chrome and the page's Lenis/Framer transforms can't shift the layout. */
import { useState } from "react";
import { createPortal } from "react-dom";
import { Icon } from "../../../lib/icons";
import { ResumeSheet } from "./ResumeSheet";

export function ResumeTab() {
  const [printing, setPrinting] = useState(false);

  function download() {
    // Mark the document so print CSS reveals only the portal copy, then print.
    setPrinting(true);
    document.body.classList.add("resume-printing");
    const cleanup = () => {
      document.body.classList.remove("resume-printing");
      setPrinting(false);
      window.removeEventListener("afterprint", cleanup);
    };
    window.addEventListener("afterprint", cleanup);
    // let the portal paint with the print class applied, then open the dialog
    window.setTimeout(() => window.print(), 80);
    // safety net if afterprint never fires (some browsers)
    window.setTimeout(cleanup, 60000);
  }

  return (
    <div className="card manage resume-tab">
      <div className="resume-tab-head">
        <div>
          <h3 style={{ margin: 0 }}>Résumé</h3>
          <p className="form-note" style={{ margin: ".2rem 0 0" }}>
            Your one-page CV, kept in sync with <code>cv-reference.md</code>. Click download, then
            choose <b>“Save as PDF”</b> as the destination in the print dialog (set margins to
            <b> None</b> and enable <b>background graphics</b> for the exact look).
          </p>
        </div>
        <button className="btn btn-primary" onClick={download} disabled={printing}>
          <Icon name="download" size={17} /> {printing ? "Preparing…" : "Download PDF"}
        </button>
      </div>

      {/* On-screen preview (scaled to fit the dashboard column). */}
      <div className="resume-preview" aria-label="Résumé preview">
        <ResumeSheet />
      </div>

      {/* Print-only copy, portalled to <body> so nothing in the app can shift it. */}
      {createPortal(
        <div className="resume-print-root" aria-hidden="true">
          <ResumeSheet />
        </div>,
        document.body,
      )}
    </div>
  );
}
