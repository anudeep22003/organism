import type { RouteObject } from "react-router";
import SceneEngineLayout from "./Layout";
import SceneEngine from ".";

export const sceneEngineRoutes: RouteObject[] = [
  {
    element: <SceneEngineLayout />,
    children: [
      {
        path: "/story/:storyId",
        element: <SceneEngine />,
      },
    ],
  },
];
