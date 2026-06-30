/* About page — bio + skills, experience timeline, and the "what you get" perks.
   A real, crawlable /about URL. */
import { AboutSection, ExperienceSection, PerksSection } from "../components/sections/staticSections";

export function AboutPage() {
  return (
    <>
      <AboutSection />
      <ExperienceSection />
      <PerksSection />
    </>
  );
}
