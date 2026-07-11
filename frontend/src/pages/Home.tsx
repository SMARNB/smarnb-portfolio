/* Public Home — ONE continuous scroll-story from the very top: the hero fold
   (hero + tech marquee) is the first stage and recedes under slide 1, then the
   showcase stories and section sheets (services / work / projects / CTA) each
   own a full screen, arriving with varied transitions. The blog teaser stays
   outside the stack because it renders nothing until posts exist. */
import { Hero } from "../components/sections/Hero";
import { featureSlides } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Work } from "../components/sections/Work";
import { PersonalProjects } from "../components/sections/PersonalProjects";
import { BlogList } from "./BlogList";
import { CtaBand } from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";

export function Home() {
  return (
    <>
      <StoryStack className="flush">
        <div className="home-fold">
          <Hero />
        </div>
        {featureSlides(true)}
        <ServicesTeaser limit={3} />
        <Work home />
        <PersonalProjects home />
        <CtaBand />
      </StoryStack>
      <BlogList home />
    </>
  );
}
