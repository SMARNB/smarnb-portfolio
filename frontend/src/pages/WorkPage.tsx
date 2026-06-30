/* Work page — selected client work + client testimonials. A real, crawlable /work
   URL. (Both sections ship in this lazy page chunk, not the landing bundle.) */
import { Work } from "../components/sections/Work";
import { Testimonials } from "../components/sections/Testimonials";

export function WorkPage() {
  return (
    <>
      <Work />
      <Testimonials />
    </>
  );
}
