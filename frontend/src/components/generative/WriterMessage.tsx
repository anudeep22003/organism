import { memo } from "react";
import { MarkdownRenderer } from "../MarkdownRenderer";
import type { BaseMessage } from "@/store/useMessageStore";

interface WriterMessageProps {
  message: BaseMessage;
  onContentLoad?: () => void;
}

export const WriterMessage = memo(
  ({ message, onContentLoad }: WriterMessageProps) => {
    return (
      <div className="bg-secondary/10 rounded-lg border border-border p-4">
        <MarkdownRenderer
          content={message.content}
          className="text-sm"
          onContentLoad={onContentLoad}
        />
      </div>
    );
  }
);

WriterMessage.displayName = "WriterMessage";
