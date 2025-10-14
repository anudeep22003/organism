import { MODE } from "@/constants";
import log from "loglevel";

// Configure root logger based on environment
if (MODE === "production") {
  log.setLevel("warn");
} else {
  log.setLevel("debug");
}

// Create named loggers for different parts of your app
export const apiLogger = log.getLogger("api");
export const mediaLogger = log.getLogger("media");
export const rootLogger = log.getLogger("root");

// Set default levels for each logger
apiLogger.setLevel("debug");
mediaLogger.setLevel("debug");
rootLogger.setLevel("debug");

// Export the default logger for general use
export default log;

// Optional: Add a function to enable debug mode globally
// Users can call this from browser console: window.enableDebugMode()
if (typeof window !== "undefined") {
  (
    window as Window &
      typeof globalThis & { enableDebugMode: () => void }
  ).enableDebugMode = () => {
    log.setLevel("debug");
    apiLogger.setLevel("debug");
    mediaLogger.setLevel("debug");
    rootLogger.setLevel("debug");
    console.info("Debug mode enabled for all loggers");
  };
}
