import { Navigate } from "react-router";
import { AuthPage, RequireAuth, RequireGuest } from "./features/auth";
import { storyRoutes } from "./features/story";
import { comicBuilderRoutes } from "./pages/comic-builder/routes";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";

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
