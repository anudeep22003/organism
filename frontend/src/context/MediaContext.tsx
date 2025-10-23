import useAudio from "@/audio/hooks/useAudio";
import type { MediaManager } from "@/audio/services/mediaManager";
import { createContext, useContext, type ReactNode } from "react";

interface MediaContextType {
  mediaManager: MediaManager | null;
}

const MediaContext = createContext<MediaContextType | null>(null);

const MediaContextProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const { mediaManager } = useAudio();
  return (
    <MediaContext.Provider value={{ mediaManager }}>
      {children}
    </MediaContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useMediaContext = () => {
  const mediaContext = useContext(MediaContext);
  if (!mediaContext) {
    throw new Error(
      "useMediaContext must be used within a MediaContextProvider"
    );
  }
  return mediaContext;
};

export default MediaContextProvider;
