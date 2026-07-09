/* About page — the portrait stays pinned (sticky) while the content blocks
   (intro, skills, experience, perks) stack and slide over each other on scroll.
   Visitors can download the CV from the portrait column. A real /about URL. */
import {
  AboutPortrait,
  AboutIntroBlock,
  AboutSkillsBlock,
  AboutXpBlock,
  AboutPerksBlock,
} from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";

export function AboutPage() {
  return (
    <section id="about">
      <div className="container about-story">
        <div className="about-photo-col">
          <AboutPortrait />
        </div>
        <StoryStack className="cards">
          <AboutIntroBlock />
          <AboutSkillsBlock />
          <AboutXpBlock />
          <AboutPerksBlock />
        </StoryStack>
      </div>
    </section>
  );
}
