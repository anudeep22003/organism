import { Navigate } from "react-router";
import { AuthPage, RequireAuth, RequireGuest } from "./features/auth";
import { sceneEngineRoutes } from "./features/scene-engine/routes";
import { storyRoutes } from "./features/story";
import { comicBuilderRoutes } from "./pages/comic-builder/routes";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";

export const routes = [
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/",
        element: <Navigate to="/scene" replace />,
      },
      {
        path: "/generative-space",
        element: <HumanAiWorkspace />,
      },
      ...sceneEngineRoutes,
      ...comicBuilderRoutes,
      ...storyRoutes,
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
