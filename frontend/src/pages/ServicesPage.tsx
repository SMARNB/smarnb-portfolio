/* Services overview page — the same scroll-story flow as Home: each showcase
   story is a full-view card, then the full catalogue, process and CTA sheets
   stack over each other (tall panels skip pinning automatically). A real,
   crawlable /services URL. */
import { featureSlides, ShowcaseHead } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { ProcessSection, CtaBand } from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";

export function ServicesPage() {
  return (
    <>
      <ShowcaseHead />
      <StoryStack>
        {featureSlides()}
        <ServicesTeaser all />
        <ProcessSection />
        <CtaBand />
      </StoryStack>
    </>
  );
}
