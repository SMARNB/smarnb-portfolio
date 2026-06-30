/* Public Home — composed from section components in the same order as index.html.
   The interactive below-the-fold sections (reviews, FAQ, contact form) are
   code-split so their JS stays out of the initial landing chunk and loads as the
   visitor scrolls; each gets a reserved-height fallback to avoid layout shift. */
import { lazy, Suspense } from "react";
import { Hero } from "../components/sections/Hero";
import { ServicesTeaser } from "../components/sections/ServicesTeaser";
import { Work } from "../components/sections/Work";
import { PersonalProjects } from "../components/sections/PersonalProjects";
import {
  Marquee,
  ProcessSection,
  PerksSection,
  AboutSection,
  ExperienceSection,
  CtaBand,
  PaymentsSection,
} from "../components/sections/staticSections";

const Testimonials = lazy(() =>
  import("../components/sections/Testimonials").then((m) => ({ default: m.Testimonials })),
);
const Faq = lazy(() => import("../components/sections/Faq").then((m) => ({ default: m.Faq })));
const Contact = lazy(() =>
  import("../components/sections/Contact").then((m) => ({ default: m.Contact })),
);

function Spacer({ h }: { h: number }) {
  return <div style={{ minHeight: h }} aria-hidden="true" />;
}

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
      <Suspense fallback={<Spacer h={640} />}>
        <Testimonials />
      </Suspense>
      <Suspense fallback={<Spacer h={420} />}>
        <Faq />
      </Suspense>
      <CtaBand />
      <Suspense fallback={<Spacer h={520} />}>
        <Contact />
      </Suspense>
      <PaymentsSection />
    </>
  );
}
