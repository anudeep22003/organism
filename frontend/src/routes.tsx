import { Navigate } from "react-router";
import {
  AuthFailurePage,
  AuthPage,
  AuthSuccessPage,
  RequireAuth,
  RequireGuest,
} from "./features/auth";
import { sceneEngineRoutes } from "./features/scene-engine/routes";
import { storiesRoutes } from "./features/scene-engine/stories/stories.routes";

export const routes = [
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/",
        element: <Navigate to="/stories" replace />,
      },
      ...storiesRoutes,
      ...sceneEngineRoutes,
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
  {
    path: "/auth/success",
    element: <AuthSuccessPage />,
  },
  {
    path: "/auth/failure",
    element: <AuthFailurePage />,
  },
];
