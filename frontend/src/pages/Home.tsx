/* Public Home — composed from section components in the same order as index.html. */
import { Hero } from "../components/sections/Hero";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Work } from "../components/sections/Work";
import { PersonalProjects } from "../components/sections/PersonalProjects";
import { Testimonials } from "../components/sections/Testimonials";
import { Faq } from "../components/sections/Faq";
import { Contact } from "../components/sections/Contact";
import {
  Marquee,
  ProcessSection,
  PerksSection,
  AboutSection,
  ExperienceSection,
  CtaBand,
  PaymentsSection,
} from "../components/sections/staticSections";

export function Home() {
  return (
    <>
      <Hero />
      <Marquee />
      <ServicesTeaser />
      <Work />
      <PersonalProjects />
      <ProcessSection />
      <AboutSection />
      <PerksSection />
      <ExperienceSection />
      <Testimonials />
      <Faq />
      <CtaBand />
      <Contact />
      <PaymentsSection />
    </>
  );
}
