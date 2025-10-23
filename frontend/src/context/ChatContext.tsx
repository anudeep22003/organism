import {
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";
import type { ReactNode } from "react";
import { useSocketContext } from "./SocketContext";
import {
  sendChatMessage,
  sendCodeMessage,
  sendDirectorMessage,
  sendWriterMessage,
  sendClaudeMessage,
} from "@/socket/messageSendHandlers";
import {
  useHumanAreaMessages,
  useMessageStore,
} from "@/store/useMessageStore";

interface ChatContextType {
  inputText: string;
  setInputText: (
    inputText: string | ((prevText: string) => string)
  ) => void;
  handleInputSendClick: () => Promise<void>;
  handleCodeSendClick: () => Promise<void>;
  handleWriterSendClick: () => Promise<void>;
  handleClaudeSendClick: () => Promise<void>;
  handleDirectorSendClick: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | null>(null);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [inputText, setInputText] = useState("");

  const { emit } = useSocketContext();

  const addMessage = useMessageStore((state) => state.addMessage);
  const humanAreaMessages = useHumanAreaMessages();
  const createStreamMessage = useMessageStore(
    (state) => state.createStreamMessage
  );

  const createChatMessageHandler = useCallback(
    (sendFn: typeof sendChatMessage) => async () => {
      await sendFn(
        inputText,
        setInputText,
        emit,
        addMessage,
        humanAreaMessages,
        createStreamMessage
      );
    },
    [
      inputText,
      setInputText,
      emit,
      addMessage,
      humanAreaMessages,
      createStreamMessage,
    ]
  );

  const handleCodeSendClick = useCallback(
    () => createChatMessageHandler(sendCodeMessage)(),
    [createChatMessageHandler]
  );

  const handleDirectorSendClick = useCallback(
    () => createChatMessageHandler(sendDirectorMessage)(),
    [createChatMessageHandler]
  );

  const handleWriterSendClick = useCallback(
    () => createChatMessageHandler(sendWriterMessage)(),
    [createChatMessageHandler]
  );

  const handleClaudeSendClick = useCallback(
    () => createChatMessageHandler(sendClaudeMessage)(),
    [createChatMessageHandler]
  );

  const handleInputSendClick = useCallback(
    () => createChatMessageHandler(sendChatMessage)(),
    [createChatMessageHandler]
  );

  return (
    <ChatContext.Provider
      value={{
        inputText,
        setInputText,
        handleInputSendClick,
        handleCodeSendClick,
        handleDirectorSendClick,
        handleWriterSendClick,
        handleClaudeSendClick,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useChatContext = () => {
  const chatContext = useContext(ChatContext);
  if (!chatContext) {
    throw new Error(
      "useChatContext must be used within a ChatProvider"
    );
  }
  return chatContext;
};
