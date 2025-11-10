import AuthPage from "./pages/auth";
import HumanAiWorkspace from "./pages/HumanAiWorkspace";
import Login from "./pages/Login";

export const routes = [
  {
    path: "/",
    element: <HumanAiWorkspace />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/auth",
    element: <AuthPage />,
  },
];
