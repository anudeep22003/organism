export const ActorListConst = [
  "assistant",
  "coder",
  "writer",
  "claude",
  "scriptwriter",
  "director",
  "manager",
  "tasknotifier",
] as const;

export type Actor = (typeof ActorListConst)[number];

export const HumanAreaActorsListConst = [
  "assistant",
  "human",
  "tasknotifier",
] as const;

export type HumanAreaActors = (typeof HumanAreaActorsListConst)[number];

export type StreamingActors = Exclude<Actor, HumanAreaActors>;
