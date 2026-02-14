import { AuthPage, RequireAuth, RequireGuest } from "./features/auth";
import { comicBuilderRoutes } from "./pages/comic-builder/routes";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";
import { storyBuilderRoutes } from "./story-builder/routes";
import { Navigate } from "react-router";

export const routes = [
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/",
        element: <Navigate to="/comic" replace />,
      },
      {
        path: "/generative-space",
        element: <HumanAiWorkspace />,
      },
      ...comicBuilderRoutes,
      ...storyBuilderRoutes,
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
