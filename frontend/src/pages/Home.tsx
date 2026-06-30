/* Public Home — a concise hub: intro, tech marquee, a services teaser, and a CTA.
   The full content lives on dedicated routes (/services, /work, /projects, /about,
   /contact, /store), each a real crawlable page. */
import { Hero } from "../components/sections/Hero";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Marquee, CtaBand } from "../components/sections/staticSections";

export function Home() {
  return (
    <>
      <Hero />
      <Marquee />
      <ServicesTeaser />
      <CtaBand />
    </>
  );
}
