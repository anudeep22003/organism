import type { RouteObject } from "react-router";
import ProjectList from "./Projects/ProjectList";

export const storyRoutes: RouteObject[] = [
  {
    path: "/story",
    element: <ProjectList />,
  },
];
