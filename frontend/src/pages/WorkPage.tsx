/* Work page — selected client work + testimonials in the scroll-story flow (the
   tall work grid scrolls naturally; testimonials slide over it). A real /work
   URL. (Both sections ship in this lazy page chunk, not the landing bundle.) */
import { Work } from "../components/sections/Work";
import { Testimonials } from "../components/sections/Testimonials";
import { StoryStack } from "../components/ui/StoryStack";

export function WorkPage() {
  return (
    <StoryStack>
      <Work />
      <Testimonials />
    </StoryStack>
  );
}
