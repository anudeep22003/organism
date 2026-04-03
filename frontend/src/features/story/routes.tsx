import type { RouteObject } from "react-router";
import ProjectHome from "./projects/ui/ProjectHome";
import ProjectList from "./projects/ui/ProjectList";
import StoryWorkspace from "./phases/story-phase/ui/StoryWorkspace";

const ROOT_PATH = "/story";

export const storyRoutes: RouteObject[] = [
  {
    path: ROOT_PATH,
    element: <ProjectList />,
  },
  {
    path: `${ROOT_PATH}/p/:projectId`,
    element: <ProjectHome />,
  },
  {
    path: `${ROOT_PATH}/p/:projectId/s/:storyId`,
    element: <StoryWorkspace />,
  },
];
