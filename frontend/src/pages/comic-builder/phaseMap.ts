import ExtractCharactersPhase from "./components/ExtractCharactersPhase";
import WriteStoryPhase from "./components/WriteStoryPhase";

/**
 * Single source of truth for phases - order matters here.
 * Everything else is derived from this config.
 */
const phaseConfig = [
  { key: "write-story", component: WriteStoryPhase },
  { key: "extract-characters", component: ExtractCharactersPhase },
] as const;

export type PhaseMapKey = (typeof phaseConfig)[number]["key"];

export const phases: PhaseMapKey[] = phaseConfig.map((p) => p.key);

const phaseMap = Object.fromEntries(
  phaseConfig.map((p) => [p.key, p.component])
) as unknown as Record<PhaseMapKey, React.ComponentType>;

export default phaseMap;
