import ProtectedLayout from "./pages/auth/ProtectedLayout";
import PublicLayout from "./pages/auth/PublicLayout";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";
import AuthPage from "./pages/auth";
import ComicBuilder from "./pages/comic-builder";

export const routes = [
  {
    element: <ProtectedLayout />,
    children: [
      {
        path: "/generative-space",
        element: <HumanAiWorkspace />,
      },
      {
        path: "/",
        element: <ComicBuilder />,
      },
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
