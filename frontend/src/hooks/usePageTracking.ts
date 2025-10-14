import { useEffect } from "react";
import { useLocation } from "react-router";
import { usePostHog } from "posthog-js/react";

export const usePageTracking = () => {
  const location = useLocation();
  const posthog = usePostHog();

  useEffect(() => {
    if (posthog) {
      posthog.capture("$pageview");
    }
  }, [location, posthog]);
};
