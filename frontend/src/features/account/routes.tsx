import type { RouteObject } from "react-router";
import StoriesLayout from "../scene-engine/stories/StoriesLayout";
import AccountPage from "./ui/AccountPage";

export const accountRoutes: RouteObject[] = [
  {
    element: <StoriesLayout />,
    children: [
      {
        path: "/account",
        element: <AccountPage />,
      },
    ],
  },
];
