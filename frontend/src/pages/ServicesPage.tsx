/* Services overview page — the scroll-story flow: showcase, full catalogue,
   process and CTA stack over each other on scroll (tall panels skip pinning
   automatically). A real, crawlable /services URL. */
import { FeatureShowcase } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { ProcessSection, CtaBand } from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";

export function ServicesPage() {
  return (
    <StoryStack>
      <FeatureShowcase />
      <ServicesTeaser all />
      <ProcessSection />
      <CtaBand />
    </StoryStack>
  );
}
