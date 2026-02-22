import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import InputBox from "@/components/InputBox/InputBox";
import PromptMessage from "./PromptMessage";
import type { PromptMessage as PromptMessageType } from "../types";

type PromptPanelProps = {
  messages: PromptMessageType[];
  onSubmit: (text: string) => void;
  isGenerating: boolean;
};

function PromptPanel({
  messages,
  onSubmit,
  isGenerating,
}: PromptPanelProps) {
  const scrollEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <ScrollArea className="flex-1 min-h-0 px-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full min-h-[200px]">
            <p className="text-sm text-muted-foreground text-center select-none">
              Begin shaping your story...
            </p>
          </div>
        ) : (
          <div className="py-4">
            {messages.map((message, index) => (
              <PromptMessage
                key={message.id}
                message={message}
                index={index}
              />
            ))}
            <div ref={scrollEndRef} />
          </div>
        )}
      </ScrollArea>

      <div className="shrink-0 p-3">
        <InputBox
          onSubmit={onSubmit}
          placeholder="Describe your vision..."
          disabled={isGenerating}
        />
      </div>
    </div>
  );
}

export default PromptPanel;
