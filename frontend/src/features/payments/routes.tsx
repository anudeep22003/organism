import type { RouteObject } from "react-router";
import StoriesLayout from "../scene-engine/stories/StoriesLayout";
import PaymentsPage from "./ui/PaymentsPage";
import PaymentsSuccessPage from "./ui/PaymentsSuccessPage";

export const paymentsRoutes: RouteObject[] = [
  {
    element: <StoriesLayout />,
    children: [
      {
        path: "/payments",
        element: <PaymentsPage />,
      },
      {
        path: "/payments/success",
        element: <PaymentsSuccessPage />,
      },
    ],
  },
];
