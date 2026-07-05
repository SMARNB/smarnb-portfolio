/* Public Home — a concise hub: intro, tech marquee, a Problem/Solution/Result
   showcase of the top strengths, a short services teaser, and a CTA. The full
   content lives on dedicated routes (/services, /work, /projects, /about,
   /contact, /store), each a real crawlable page. */
import { Hero } from "../components/sections/Hero";
import { FeatureShowcase } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Marquee, CtaBand } from "../components/sections/staticSections";

export function Home() {
  return (
    <>
      <Hero />
      <Marquee />
      <FeatureShowcase />
      <ServicesTeaser limit={3} />
      <CtaBand />
    </>
  );
}
