/* Public Home — hero + tech marquee, then one continuous scroll-story: each
   showcase story is its own full-view card, followed by the section sheets
   (services / work / projects / CTA), every one pinning while the next slides
   over it. The blog teaser stays outside the stack because it renders nothing
   until posts exist. */
import { Hero } from "../components/sections/Hero";
import { featureSlides, ShowcaseHead } from "../components/sections/FeatureShowcase";
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
      <ShowcaseHead />
      <StoryStack>
        {featureSlides()}
        <ServicesTeaser limit={3} />
        <Work home />
        <PersonalProjects home />
        <CtaBand />
      </StoryStack>
      <BlogList home />
    </>
  );
}
