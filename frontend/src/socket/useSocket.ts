import { useEffect, useRef, useCallback, useState } from "react";
import io from "socket.io-client";
import { BACKEND_URL } from "@/constants";
import { Socket } from "socket.io-client";
import { type Envelope } from "@/socket/types/envelope";
import { ActorListConst, type Actor } from "./types/actors";
import { useMessageStore } from "@/store/useMessageStore";

export const useSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  const updateStreamingMessage = useMessageStore(
    (state) => state.updateStreamingMessage
  );
  const removeStreamingActor = useMessageStore(
    (state) => state.removeStreamingActor
  );

  const createStreamMessage = useMessageStore(
    (state) => state.createStreamMessage
  );

  const onStreamChunk = useCallback(
    (rawMessage: string) => {
      try {
        const envelope: Envelope<{ delta: string }> =
          JSON.parse(rawMessage);
        updateStreamingMessage(envelope);
      } catch (error) {
        console.error("Error parsing stream chunk:", error, rawMessage);
      }
    },
    [updateStreamingMessage]
  );

  const onStreamEnd = useCallback(
    (actor: Actor) => {
      removeStreamingActor(actor);
    },
    [removeStreamingActor]
  );

  const onStreamStart = useCallback(
    (rawMessage: string) => {
      try {
        const parsed_envelope = JSON.parse(rawMessage) as Envelope<{
          delta: "start";
        }>;

        if (!parsed_envelope.streamId || !parsed_envelope.requestId) {
          throw new Error(
            `Stream ID ${parsed_envelope.streamId} or request ID ${parsed_envelope.requestId} is missing`
          );
        }

        createStreamMessage(
          parsed_envelope.streamId,
          parsed_envelope.requestId,
          parsed_envelope.actor
        );
      } catch (error) {
        console.error("Error parsing stream start:", error, rawMessage);
      }
    },
    [createStreamMessage]
  );

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
    const socket = io(BACKEND_URL, {
      transports: ["websocket", "polling"],
      autoConnect: true,
      timeout: 20000,
      reconnection: true,
    });

    socket.on("connect", () => {
      setIsConnected(true);
      socket.emit("hello", "world");
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
    });

    for (const actor of ActorListConst) {
      socket.on(`s2c.${actor}.stream.chunk`, (rawMessage: string) => {
        onStreamChunk(rawMessage);
      });

      socket.on(`s2c.${actor}.stream.end`, () => {
        onStreamEnd(actor);
      });

      socket.on(`s2c.${actor}.stream.start`, (rawMessage: string) => {
        onStreamStart(rawMessage);
      });
    }

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [onStreamChunk, onStreamEnd, createStreamMessage, onStreamStart]);

  return {
    isConnected,
    emit,
    socket: socketRef.current,
  };
};
