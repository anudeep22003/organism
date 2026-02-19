import type { RouteObject } from "react-router";
import ProjectHome from "./Projects/ProjectHome";
import ProjectList from "./Projects/ProjectList";
import StoryPhasePage from "./StoryPhase/ui/StoryPhasePage";

export const storyRoutes: RouteObject[] = [
  {
    path: "/story",
    element: <ProjectList />,
  },
  {
    path: "/story/:projectId",
    element: <ProjectHome />,
  },
  {
    path: "/story/:storyId/create",
    element: <StoryPhasePage />,
  },
];
