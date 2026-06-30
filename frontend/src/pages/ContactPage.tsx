/* Contact page — custom-request form, FAQ, and payment/trust info. A real,
   crawlable /contact URL. (Form + FAQ ship in this lazy page chunk.) */
import { Contact } from "../components/sections/Contact";
import { Faq } from "../components/sections/Faq";
import { PaymentsSection } from "../components/sections/staticSections";

export function ContactPage() {
  return (
    <>
      <Contact />
      <Faq />
      <PaymentsSection />
    </>
  );
}
