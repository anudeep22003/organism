import type { RouteObject } from "react-router";
import StoriesLayout from "./StoriesLayout";
import StoriesView from "./StoriesView";

export const storiesRoutes: RouteObject[] = [
  {
    element: <StoriesLayout />,
    children: [
      {
        path: "/stories",
        element: <StoriesView />,
      },
    ],
  },
];
