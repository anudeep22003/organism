import type { RouteObject } from "react-router";
import SceneEngine from ".";

export const sceneEngineRoutes: RouteObject[] = [
  {
    path: "/scene",
    element: <SceneEngine />,
  },
];
