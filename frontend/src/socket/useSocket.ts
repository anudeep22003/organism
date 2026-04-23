import { useAuth } from "@/features/auth_v2";
import { useCallback, useEffect, useRef, useState } from "react";
import { Socket } from "socket.io-client";

export const useSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const [connectionError, setConnectionError] = useState(false);
  const { isAuthenticated } = useAuth();

  const emit = useCallback(
    (event: string, data?: unknown, ack?: (ack: string) => void) => {
      if (ack) {
        socketRef.current?.emit(event, data, ack);
      } else {
        socketRef.current?.emit(event, data);
      }
    },
    []
  );

  useEffect(() => {
    socketRef.current?.disconnect();
    socketRef.current = null;
    setIsConnected(false);
    setConnectionError(false);

    if (!isAuthenticated) {
      return;
    }

    console.warn(
      "Socket connection is disabled until cookie-based socket auth is implemented."
    );
  }, [isAuthenticated]);

  return {
    isConnected,
    emit,
    socket: socketRef.current,
    connectionError,
  };
};
