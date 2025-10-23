import { useMessageStore } from "@/store/useMessageStore";
import { useEffect, type ReactNode } from "react";

const MessageMaintenanceProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const { clearOldMessages } = useMessageStore();
  // Periodic cleanup of old messages
  useEffect(() => {
    const interval = setInterval(() => {
      clearOldMessages();
    }, 60000); // Clear old messages every minute

    return () => clearInterval(interval);
  }, [clearOldMessages]);

  return <>{children}</>;
};

export default MessageMaintenanceProvider;
