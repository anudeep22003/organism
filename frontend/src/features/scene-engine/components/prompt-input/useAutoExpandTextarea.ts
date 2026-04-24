import { useCallback, useRef } from "react";

const MAX_HEIGHT_RATIO = 0.8;

export function useAutoExpandTextarea() {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const maxHeight = window.innerHeight * MAX_HEIGHT_RATIO;
    const nextHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY =
      textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, []);

  const resetHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.overflowY = "hidden";
  }, []);

  return { textareaRef, adjustHeight, resetHeight };
}
