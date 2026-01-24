// Consolidated comic state types - flat structure matching backend schema

import type { PhaseMapKey } from "../phaseMap";

// === Status Types ===

export type EntityStatus = "idle" | "streaming" | "completed" | "error";

// === Base Types ===

type BaseComicStateEntity = {
  id: string;
  userInputText: string[];
  status: EntityStatus;
};

export type Artifact = BaseComicStateEntity & {
  url: string | null;
};

// === Domain Types ===

export type Story = BaseComicStateEntity & {
  storyText: string;
};

export type CharacterType =
  | "humanoid"
  | "creature"
  | "concept"
  | "object";

export type CharacterRole =
  | "protagonist"
  | "antagonist"
  | "supporting"
  | "minor";

export type Character = BaseComicStateEntity & {
  name: string;
  brief: string;
  characterType: CharacterType;
  era: string;
  visualForm: string;
  colorPalette: string;
  distinctiveMarkers: string;
  demeanor: string;
  role: CharacterRole;
  render: Artifact | null;
};

export type ComicPanel = BaseComicStateEntity & {
  background: string;
  characters: string[]; // character names
  dialogue: string;
  render: Artifact | null;
};

// === State Shape (flat - no nesting) ===

export type ConsolidatedComicState = {
  story: Story;
  characters: Record<string, Character>;
  panels: ComicPanel[];
};

export type ComicState = {
  // Project metadata (was in Comic type before)
  projectId: string | null;
  projectName: string | null;
  createdAt: string | null;
  updatedAt: string | null;

  // Phase tracking
  currentPhase: PhaseMapKey;

  // Domain data (flat - directly accessible)
  story: Story | null;
  characters: Record<string, Character>;
  panels: ComicPanel[];

  // Fetch status for loading project
  fetchStatus: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};
