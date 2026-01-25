import ExtractCharactersPhase from "./components/phases/ExtractCharactersPhase";
import GenerateCharacterPhase from "./components/phases/GenerateCharacterPhase";
import GeneratePanelsPhase from "./components/phases/GeneratePanelsPhase";
import RenderPanelsPhase from "./components/phases/RenderPanelsPhase";
import WriteStoryPhase from "./components/phases/WriteStoryPhase";

/**
 * Single source of truth for phases - order matters here.
 * Everything else is derived from this config.
 */
const phaseConfig = [
  { key: "write-story", component: WriteStoryPhase },
  { key: "extract-characters", component: ExtractCharactersPhase },
  { key: "generate-characters", component: GenerateCharacterPhase },
  { key: "generate-panels", component: GeneratePanelsPhase },
  { key: "render-panels", component: RenderPanelsPhase },
] as const;

export type PhaseMapKey = (typeof phaseConfig)[number]["key"];

export const phases: PhaseMapKey[] = phaseConfig.map((p) => p.key);

const phaseMap = Object.fromEntries(
  phaseConfig.map((p) => [p.key, p.component])
) as unknown as Record<PhaseMapKey, React.ComponentType>;

export default phaseMap;
