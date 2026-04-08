import type { RouteObject } from "react-router";
import StoryWorkspace from "./phases/story-phase/ui/StoryWorkspace";
import ProjectHome from "./projects/ui/ProjectHome";
import ProjectList from "./projects/ui/ProjectList";

const ROOT_PATH = "/legacy/story";

export const legacyStoryRoutes: RouteObject[] = [
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
