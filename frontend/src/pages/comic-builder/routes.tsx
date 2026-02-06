import type { RouteObject } from "react-router";
import ComicBuilder from "./components/ComicBuilder";
import ProjectsPage from "./ProjectsPage";

// const ROOT_PATH = "/comic-builder";
const ROOT_PATH = "/";

export const comicBuilderRoutes: RouteObject[] = [
  {
    path: ROOT_PATH,
    element: <ProjectsPage />,
  },
  {
    path: `${ROOT_PATH}/:projectId`,
    element: <ComicBuilder />,
  },
];
