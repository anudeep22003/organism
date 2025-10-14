import { memo } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { BaseMessage } from "@/store/useMessageStore";

export const CodeMessage = memo(({ message }: { message: BaseMessage }) => {
  return (
    <div className="bg-secondary/10 rounded-lg border border-border overflow-hidden">
      <SyntaxHighlighter
        language="typescript"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: "1rem",
          fontSize: "0.875rem",
          backgroundColor: "#1e1e1e",
          borderRadius: "0.5rem",
        }}
        showLineNumbers
        wrapLines
        lineNumberStyle={{
          minWidth: "3em",
          paddingRight: "1em",
          color: "#858585",
        }}
      >
        {message.content}
      </SyntaxHighlighter>
    </div>
  );
});

CodeMessage.displayName = "CodeMessage";