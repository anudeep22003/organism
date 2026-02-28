import type { ReactNode } from "react";

export type RefinePayload = {
  text: string;
  attachments: File[];
};

export type ArtifactCardProps = {
  title: string;
  prompt?: string;
  content: ReactNode;
  headerActions?: ReactNode;
  isStale?: boolean;
  isLoading?: boolean;
  collapsible?: boolean;
  enableAttachments?: boolean;
  onRefine?: (payload: RefinePayload) => void;
  className?: string;
};
