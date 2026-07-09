/* Public Home — hero + tech marquee, then the scroll-story: each section is a
   sheet that pins and is covered by the next as you scroll (StoryStack). The blog
   teaser stays outside the stack because it renders nothing until posts exist. */
import { Hero } from "../components/sections/Hero";
import { FeatureShowcase } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Work } from "../components/sections/Work";
import { PersonalProjects } from "../components/sections/PersonalProjects";
import { BlogList } from "./BlogList";
import { Marquee, CtaBand } from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";

export function Home() {
  return (
    <>
      <Hero />
      <Marquee />
      <StoryStack>
        <FeatureShowcase />
        <ServicesTeaser limit={3} />
        <Work home />
        <PersonalProjects home />
        <CtaBand />
      </StoryStack>
      <BlogList home />
    </>
  );
}
