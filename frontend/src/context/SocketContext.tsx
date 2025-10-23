import { useSocket } from "@/socket/useSocket";
import { createContext, useContext, type ReactNode } from "react";
import type { Socket } from "socket.io-client";

interface SocketContextType {
  isConnected: boolean;
  emit: (event: string, data?: unknown) => void;
  socket: Socket | null;
  connectionError: boolean;
}

const SocketContext = createContext<SocketContextType | null>(null);

export const SocketProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const { isConnected, emit, socket, connectionError } = useSocket();

  return (
    <SocketContext.Provider
      value={{
        isConnected,
        emit,
        socket,
        connectionError,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useSocketContext = () => {
  const socketContext = useContext(SocketContext);
  if (!socketContext) {
    throw new Error(
      "useSocketContext must be used within a SocketProvider"
    );
  }
  return socketContext;
};
