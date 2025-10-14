import { useHumanAreaMessages } from "@/store/useMessageStore";
import { useEffect, useRef, useMemo, useCallback } from "react";
import { MessageInput } from "./MessageInput";
import { MarkdownRenderer } from "./MarkdownRenderer";

const HumaAreaHeader = () => {
  return (
    <div className="p-4 border-b border-border">
      <h2 className="text-lg font-medium">🔍 Human-AI Workspace</h2>
    </div>
  );
};

const MessageList = () => {
  const humanAreaMessages = useHumanAreaMessages();
  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    // Use setTimeout to ensure DOM is updated after markdown rendering
    setTimeout(() => {
      messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 0);
  }, []);

  const messagesLength = humanAreaMessages.length;
  const lastMessageContent =
    humanAreaMessages[humanAreaMessages.length - 1]?.content || "";

  useEffect(() => {
    scrollToBottom();
  }, [messagesLength, lastMessageContent, scrollToBottom]);

  const memoizedMessages = useMemo(() => {
    return humanAreaMessages.map((message) => (
      <div
        key={message.id}
        className={`flex ${
          message.type === "human" ? "justify-end" : "justify-start"
        }`}
      >
        <div
          className={`rounded-lg p-3 ${
            message.type === "human"
              ? "max-w-[80%] bg-primary text-primary-foreground"
              : "w-full bg-muted/50 border border-border"
          }`}
        >
          <MarkdownRenderer
            content={message.content}
            className="text-sm"
            onContentLoad={scrollToBottom}
          />
        </div>
      </div>
    ));
  }, [humanAreaMessages, scrollToBottom]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {memoizedMessages}
      <div ref={messageEndRef} />
    </div>
  );
};

export const HumanArea = () => {
  return (
    <div className="flex flex-col h-full bg-background border-r border-border">
      <HumaAreaHeader />
      <MessageList />
      <div className="p-4 border-t border-border">
        <MessageInput />
      </div>
    </div>
  );
};
