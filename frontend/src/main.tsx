import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { PostHogProvider } from "posthog-js/react";
import { POSTHOG_KEY, POSTHOG_URL, MODE } from "./config";
import "@/lib/logger"; // Initialize logger
import App from "./app/App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {MODE === "development" ? (
      <App />
    ) : (
      <PostHogProvider
        apiKey={POSTHOG_KEY}
        options={{
          api_host: POSTHOG_URL,
          capture_exceptions: false,
          debug: false,
          capture_pageview: false,
          capture_pageleave: false,
          autocapture: false,
        }}
      >
        <App />
      </PostHogProvider>
    )}
  </StrictMode>
);
