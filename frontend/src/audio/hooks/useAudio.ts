import { WhisperTranscriber } from "../services/transcriber";
import { MediaManager } from "../services/mediaManager";
import { useRef } from "react";

const useAudio = () => {
  const mediaManagerRef = useRef<MediaManager>(
    new MediaManager(new WhisperTranscriber())
  );

  return {
    mediaManager: mediaManagerRef.current,
    startRecording: () => mediaManagerRef.current.startRecording(),
    stopRecording: () => mediaManagerRef.current.stopRecording(),
  };
};

export default useAudio;
