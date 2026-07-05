/* Services overview page — a Problem/Solution/Result showcase of the top
   strengths, the full service catalogue, how-it-works process, and a CTA into the
   store. A real, crawlable /services URL. */
import { FeatureShowcase } from "../components/sections/FeatureShowcase";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { ProcessSection, CtaBand } from "../components/sections/staticSections";

export function ServicesPage() {
  return (
    <>
      <FeatureShowcase />
      <ServicesTeaser all />
      <ProcessSection />
      <CtaBand />
    </>
  );
}
