import type { RouteObject } from "react-router";
import ComicBuilder from "./pages/ComicBuilder";
import Projects from "./pages/Projects";

// const ROOT_PATH = "/comic-builder";
const ROOT_PATH = "/";

export const comicBuilderRoutes: RouteObject[] = [
  {
    path: ROOT_PATH,
    element: <Projects />,
  },
  {
    path: `${ROOT_PATH}/:projectId`,
    element: <ComicBuilder />,
  },
];
