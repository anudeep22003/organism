import ExtractCharactersPhase from "./components/ExtractCharactersPhase";
import WriteStoryPhase from "./components/WriteStoryPhase";

const phaseMap: Record<string, React.ComponentType> = {
  "write-story": WriteStoryPhase,
  "extract-characters": ExtractCharactersPhase,
};
export type PhaseMapKey = keyof typeof phaseMap;

export const phases: PhaseMapKey[] = Object.keys(
  phaseMap
) as PhaseMapKey[];

export default phaseMap;
