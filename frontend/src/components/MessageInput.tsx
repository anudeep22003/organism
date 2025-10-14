import { useAppContext } from "@/context/AppContext";
import { Button } from "@/components/ui/button";
import { useRef, useEffect, useCallback, useState } from "react";
import { MicIcon } from "lucide-react";
import AudioWaveform, {
  type AudioWaveformHandle,
} from "../audio/components/AudioWaveform";
import { mediaLogger } from "@/lib/logger";

export const MessageInput = () => {
  const {
    inputText,
    setInputText,
    handleInputSendClick,
    handleDirectorSendClick,
    mediaManager,
  } = useAppContext();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const waveformRef = useRef<AudioWaveformHandle>(null);

  const handleRecordClick = useCallback(async () => {
    if (isRecording) {
      setIsRecording(false);
      const result = await mediaManager?.stopRecording();
      if (result?.success && result.text) {
        // so that the double new line is not added when inputText is empty
        if (inputText) {
          setInputText((prevText) => prevText + "\n\n" + result.text);
        } else {
          setInputText(result.text);
        }
      } else if (result && !result.success) {
        // Handle error - maybe show a toast or alert
        mediaLogger.error("Failed to stop recording:", result.error);
      }
    } else {
      const result = await mediaManager?.startRecording();
      if (result?.success) {
        setIsRecording(true);
      } else if (result && !result.success) {
        // Handle error - maybe show a toast or alert
        mediaLogger.error("Failed to start recording:", result.error);
      }
    }
  }, [mediaManager, isRecording, setInputText, inputText]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newInputText = e.target.value;
      setInputText(newInputText);
    },
    [setInputText]
  );

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [inputText]);

  const isSubmitEnabled = inputText.trim() !== "";

  const handleSubmit = useCallback(() => {
    if (isSubmitEnabled) {
      // handleInputSendClick();
      handleDirectorSendClick();
    }
  }, [isSubmitEnabled, handleDirectorSendClick]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && isSubmitEnabled) {
        handleSubmit();
      }
    },
    [handleSubmit, isSubmitEnabled]
  );

  useEffect(() => {
    if (!mediaManager) return;

    // Set up visualization callback
    const handleVisualizationData = (buffer: Float32Array) => {
      if (waveformRef.current) {
        waveformRef.current.drawWaveform(buffer);
      } else {
        console.warn("waveformRef.current is null");
      }
    };

    mediaManager.setVisualizationCallback(handleVisualizationData);
  }, [mediaManager]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 mb-2">
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message here..."
          className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring resize-none overflow-hidden min-h-[40px]"
          rows={1}
        />
        <Button
          onClick={handleSubmit}
          disabled={!isSubmitEnabled}
          size="sm"
        >
          Send
        </Button>
        <Button
          onClick={handleRecordClick}
          size="sm"
          className={isRecording ? "bg-red-500 hover:bg-red-600" : ""}
        >
          <MicIcon className="w-4 h-4" />{" "}
          {isRecording ? "Stop" : "Record"}
        </Button>
      </div>

      {/* Add the waveform visualization */}
      {isRecording && (
        <AudioWaveform
          ref={waveformRef}
          width={600}
          height={150}
          backgroundColor="#0a0a0a"
          waveColor="#00ff88"
          lineWidth={2}
        />
      )}
    </div>
  );
};
