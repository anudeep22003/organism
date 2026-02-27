import type { ReactNode } from "react";

export type ArtifactCardProps = {
  title: string;
  content: ReactNode;
  isStale?: boolean;
  isLoading?: boolean;
  collapsible?: boolean;
  onRefine?: (text: string) => void;
  className?: string;
};
