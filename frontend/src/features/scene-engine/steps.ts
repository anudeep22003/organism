import type { StepDef } from "./types";
import PlaceholderStep from "./steps/PlaceholderStep";

export const SCENE_STEPS: StepDef[] = [
  { id: 1, label: "Story",                component: PlaceholderStep },
  { id: 2, label: "Character Extraction", component: PlaceholderStep },
  { id: 3, label: "Character Rendering",  component: PlaceholderStep },
  { id: 4, label: "Scene Extraction",     component: PlaceholderStep },
  { id: 5, label: "Scene Rendering",      component: PlaceholderStep },
  { id: 6, label: "Review",               component: PlaceholderStep },
  { id: 7, label: "Export",               component: PlaceholderStep },
];
