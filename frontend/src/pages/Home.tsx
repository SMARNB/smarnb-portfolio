/* Public Home — a concise hub: intro, tech marquee, a Problem/Solution/Result
   showcase, then a capped 3-card preview of every content page (services, work,
   projects, blog), each linking to its full route. */
import { Hero } from "../components/sections/Hero";
import { FeatureShowcase } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Work } from "../components/sections/Work";
import { PersonalProjects } from "../components/sections/PersonalProjects";
import { BlogList } from "./BlogList";
import { Marquee, CtaBand } from "../components/sections/staticSections";

export function Home() {
  return (
    <>
      <Hero />
      <Marquee />
      <FeatureShowcase />
      <ServicesTeaser limit={3} />
      <Work home />
      <PersonalProjects home />
      <BlogList home />
      <CtaBand />
    </>
  );
}
