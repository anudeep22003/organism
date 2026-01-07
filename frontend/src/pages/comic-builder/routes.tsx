import type { RouteObject } from "react-router";
import ComicBuilder from "./components/ComicBuilder";
import Projects from "./index";

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
