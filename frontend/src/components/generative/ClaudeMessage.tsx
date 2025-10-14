import { memo, useMemo } from "react";
import type { BaseMessage } from "@/store/useMessageStore";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

const formatJsonInContent = (content: string): string => {
  // Find JSON code blocks and format them
  return content.replace(
    /```json\n([\s\S]*?)\n```/g,
    (match, jsonContent) => {
      try {
        // Parse and re-stringify with proper formatting
        const parsed = JSON.parse(jsonContent.trim());
        const formatted = JSON.stringify(parsed, null, 2);
        return `\`\`\`json\n${formatted}\n\`\`\``;
      } catch {
        // If parsing fails, return original content
        return match;
      }
    }
  );
};

export const ClaudeMessage = memo(
  ({ message }: { message: BaseMessage }) => {
    const formattedContent = useMemo(
      () => formatJsonInContent(message.content),
      [message.content]
    );

    return (
      <div className="bg-black rounded-lg border border-gray-900 overflow-hidden shadow-lg">
        {/* Terminal Header */}
        <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center gap-2">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <div className="text-gray-400 text-sm font-medium ml-2">
            Claude Response
          </div>
        </div>

        {/* Terminal Content */}
        <div className="p-4 font-mono text-sm text-green-400 bg-black overflow-hidden">
          <MarkdownRenderer content={formattedContent} />
        </div>
      </div>
    );
  }
);

ClaudeMessage.displayName = "ClaudeMessage";
