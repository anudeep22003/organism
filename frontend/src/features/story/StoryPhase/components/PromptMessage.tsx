import type { PromptMessage as PromptMessageType } from "../types";

type PromptMessageProps = {
  message: PromptMessageType;
  index: number;
};

function PromptMessage({ message }: PromptMessageProps) {
  return (
    <div className="group py-2">
      <div className="rounded-lg bg-muted border border-border px-3.5 py-2.5">
        <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
          {message.text}
        </p>
      </div>
      <span className="text-[10px] text-muted-foreground/50 mt-1.5 block opacity-0 group-hover:opacity-100 transition-opacity">
        {new Date(message.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
    </div>
  );
}

export default PromptMessage;
