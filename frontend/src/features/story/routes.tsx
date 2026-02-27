import type { RouteObject } from "react-router";
import ProjectHome from "./Projects/ProjectHome";
import ProjectList from "./Projects/ProjectList";
import StoryWorkspace from "./StoryPhase/StoryWorkspace";

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
