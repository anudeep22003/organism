import { useEffect, useRef, useMemo, memo, useCallback } from "react";
import type { BaseMessage } from "@/store/useMessageStore";
import type { Actor } from "@/socket/envelopeType";
import { actorRegistry } from "./Registry";
import { TabsContent } from "../ui/tabs";

interface ActorContentProps {
  type: Actor;
  allMessages: BaseMessage[];
}

export const ActorContent = memo(
  ({ type, allMessages }: ActorContentProps) => {
    const messageEndRef = useRef<HTMLDivElement>(null);

    const actorMessages = useMemo(() => {
      return allMessages.filter((m) => m.type === type);
    }, [allMessages, type]);

    const renderTabContent = useCallback(
      (actor: Actor) => {
        if (actor === "assistant") {
          return null;
        }
        const Component = actorRegistry[actor].component;
        return actorMessages.map((message) => (
          <Component key={message.id} message={message} />
        ));
      },
      [actorMessages]
    );

    const scrollToBottom = useCallback(() => {
      // Use setTimeout to ensure DOM is updated after markdown rendering
      setTimeout(() => {
        messageEndRef.current?.scrollIntoView({
          behavior: "smooth",
        });
      }, 10);
    }, []);

    const messagesLength = actorMessages.length;
    const lastMessageContent =
      actorMessages[actorMessages.length - 1]?.content || "";

    useEffect(() => {
      scrollToBottom();
    }, [messagesLength, lastMessageContent, scrollToBottom]);

    return (
      <TabsContent key={type} value={type} className="flex-1 mt-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {renderTabContent(type)}
          <div ref={messageEndRef} />
        </div>
      </TabsContent>
    );
  }
);

ActorContent.displayName = "TabContent";
