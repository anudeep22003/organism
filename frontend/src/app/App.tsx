import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { RouterProvider } from "react-router";
import { RootProvider } from "./RootProvider";
import { router } from "./router";

export default function App() {
  return (
    <RootProvider>
      <RouterProvider router={router} />
      <ReactQueryDevtools
        initialIsOpen={false}
        buttonPosition="top-left"
        theme="system"
      />
    </RootProvider>
  );
}
