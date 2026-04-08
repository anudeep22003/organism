import { Navigate } from "react-router";
import { AuthPage, RequireAuth, RequireGuest } from "./features/auth";
import { sceneEngineRoutes } from "./features/scene-engine/routes";
import { storiesRoutes } from "./features/scene-engine/stories/stories.routes";
import { legacyStoryRoutes } from "./features/story";
import { comicBuilderRoutes } from "./pages/comic-builder/routes";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";

export const routes = [
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/",
        element: <Navigate to="/stories" replace />,
      },
      {
        path: "/generative-space",
        element: <HumanAiWorkspace />,
      },
      ...storiesRoutes,
      ...sceneEngineRoutes,
      ...comicBuilderRoutes,
      ...legacyStoryRoutes,
    ],
  },
  {
    element: <RequireGuest />,
    children: [
      {
        path: "/auth",
        element: <AuthPage />,
      },
    ],
  },
];
