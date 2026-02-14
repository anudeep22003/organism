import { RootProvider } from "@/context/RootProvider";
import { router } from "@/router";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { RouterProvider } from "react-router";

export default function App() {
  return (
    <RootProvider>
      <RouterProvider router={router} />
      <ReactQueryDevtools
        initialIsOpen={false}
        buttonPosition="bottom-left"
        theme="system"
      />
    </RootProvider>
  );
}
