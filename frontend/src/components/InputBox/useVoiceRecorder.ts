import { useCallback, useRef, useState } from "react";
import { MediaManager } from "@/lib/audio/services/mediaManager";
import { WhisperTranscriber } from "@/lib/audio/services/transcriber";

type RecordingState = "idle" | "recording" | "transcribing";

export function useVoiceRecorder(
  onTranscription: (text: string) => void,
) {
  const [recordingState, setRecordingState] =
    useState<RecordingState>("idle");
  const [visualizationData, setVisualizationData] =
    useState<Float32Array | null>(null);
  const mediaManagerRef = useRef<MediaManager | null>(null);

  const getMediaManager = useCallback(() => {
    if (!mediaManagerRef.current) {
      const transcriber = new WhisperTranscriber();
      mediaManagerRef.current = new MediaManager(transcriber);
      mediaManagerRef.current.setVisualizationCallback(
        setVisualizationData,
      );
    }
    return mediaManagerRef.current;
  }, []);

  const startRecording = useCallback(async () => {
    const manager = getMediaManager();
    const result = await manager.startRecording();
    if (result.success) {
      setRecordingState("recording");
    }
  }, [getMediaManager]);

  const stopRecording = useCallback(async () => {
    const manager = getMediaManager();
    setRecordingState("transcribing");
    const result = await manager.stopRecording();
    setRecordingState("idle");
    setVisualizationData(null);
    if (result.success) {
      onTranscription(result.text);
    }
  }, [getMediaManager, onTranscription]);

  const toggleRecording = useCallback(async () => {
    if (recordingState === "recording") {
      await stopRecording();
    } else if (recordingState === "idle") {
      await startRecording();
    }
  }, [recordingState, startRecording, stopRecording]);

  return {
    recordingState,
    visualizationData,
    toggleRecording,
  };
}
