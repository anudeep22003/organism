import type { RouteObject } from "react-router";
import { Projects } from "./Projects";

export const storyRoutes: RouteObject[] = [
  {
    path: "/story",
    element: <Projects />,
  },
];
