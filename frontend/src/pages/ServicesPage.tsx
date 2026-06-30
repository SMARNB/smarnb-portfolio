/* Services overview page — the full service catalogue, how-it-works process, and a
   CTA into the store. A real, crawlable /services URL. */
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { ProcessSection, CtaBand } from "../components/sections/staticSections";

export function ServicesPage() {
  return (
    <>
      <ServicesTeaser all />
      <ProcessSection />
      <CtaBand />
    </>
  );
}
