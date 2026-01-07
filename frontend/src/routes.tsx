import AuthPage from "./pages/auth";
import ProtectedLayout from "./pages/auth/ProtectedLayout";
import PublicLayout from "./pages/auth/PublicLayout";
import { comicBuilderRoutes } from "./pages/comic-builder/routes";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";

export const routes = [
  {
    element: <ProtectedLayout />,
    children: [
      {
        path: "/generative-space",
        element: <HumanAiWorkspace />,
      },
      ...comicBuilderRoutes,
    ],
  },
  {
    element: <PublicLayout />,
    children: [
      {
        path: "/auth",
        element: <AuthPage />,
      },
    ],
  },
];
