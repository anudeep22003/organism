import type { StepDef } from "./types";
import PlaceholderStep from "./steps/PlaceholderStep";
import StoryStep from "./steps/story/StoryStep";
import CharacterExtractionStep from "./steps/character/extraction/CharacterExtractionStep";
import CharacterRenderingStep from "./steps/character/rendering/CharacterRenderingStep";

export const SCENE_STEPS: StepDef[] = [
  { id: 1, label: "Story",                component: StoryStep },
  { id: 2, label: "Character Extraction", component: CharacterExtractionStep },
  { id: 3, label: "Character Rendering",  component: CharacterRenderingStep },
  { id: 4, label: "Scene Extraction",     component: PlaceholderStep },
  { id: 5, label: "Scene Rendering",      component: PlaceholderStep },
  { id: 6, label: "Review",               component: PlaceholderStep },
  { id: 7, label: "Export",               component: PlaceholderStep },
];
