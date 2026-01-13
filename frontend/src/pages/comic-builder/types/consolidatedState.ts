// new consolidated comic state types

import type { Project } from "./project";

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

type BaseComicStateEntity = {
  id: string;
  userInputText: string[];
};

export type Story = BaseComicStateEntity & {
  storyText: string;
};

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
  renderUrls: string[];
};

export type ComicPanel = BaseComicStateEntity & {
  imageUrl: string;
  text: string;
  characters: string[]; // UUIDs of characters
  background: string;
  foreground: string;
  border: string;
  shadow: string;
  glow: string;
  renderUrls: string[];
};

export type ConsolidatedComicState = {
  story: Story;
  characters: Record<string, Character>; // keyed by UUID
  panels: ComicPanel[];
};

export type Comic = Project & {
  state: ConsolidatedComicState;
};

export type ComicState = {
  comic: Comic | null;
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};
