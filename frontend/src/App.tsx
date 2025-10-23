import { RouterProvider } from "react-router";
import { RootProvider } from "@/context/RootProvider";
import { router } from "@/router";

export default function App() {
  return (
    <RootProvider>
      <RouterProvider router={router} />
    </RootProvider>
  );
}
