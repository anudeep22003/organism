import type { PromptMessage as PromptMessageType } from "../../../api/story-phase.types";

type PromptMessageProps = {
  message: PromptMessageType;
  index: number;
};

function PromptMessage({ message, index }: PromptMessageProps) {
  return (
    <div className="group relative py-3">
      {index > 0 && (
        <div className="absolute top-0 left-0 right-0 h-px bg-border/30" />
      )}
      <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
        {message.text}
      </p>
      <span className="text-[10px] text-muted-foreground/40 mt-1 block opacity-0 group-hover:opacity-100 transition-opacity">
        {new Date(message.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
    </div>
  );
}

export default PromptMessage;
