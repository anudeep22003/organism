import ProtectedLayout from "./pages/auth/ProtectedLayout";
import PublicLayout from "./pages/auth/PublicLayout";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";
import AuthPage from "./pages/auth";

export const routes = [
  {
    element: <ProtectedLayout />,
    children: [
      {
        path: "/",
        element: <HumanAiWorkspace />,
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
