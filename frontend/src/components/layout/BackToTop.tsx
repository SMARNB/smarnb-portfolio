/* Back-to-top button — appears after scrolling down; smooth-scrolls to the top
   (via Lenis when active). Sits below the chat launcher (see chat.css). */
import { useEffect, useState } from "react";
import { Icon } from "../../lib/icons";
import { scrollToTarget } from "../../lib/lenis";

export function BackToTop() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 600);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <button
      className={`to-top${show ? " show" : ""}`}
      aria-label="Back to top"
      onClick={() => scrollToTarget(0)}
    >
      <Icon name="top" size={20} />
    </button>
  );
}
