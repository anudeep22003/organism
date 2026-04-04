import type { ComponentType } from "react";

export type StepDef = {
  id: number;
  label: string;
  component: ComponentType;
};
