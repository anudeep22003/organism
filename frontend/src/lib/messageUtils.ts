import type { TypedMessage } from "@/store/useMessageStore";

export const returnUrlIfExists = (text: string): string | null => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const match = text.match(urlRegex);
  return match ? match[0] : null;
};

export const prepareCodeMessage = async (
  text: string
): Promise<object> => {
  try {
    // Read files from the public folder
    const [packageResponse, contextResponse, componentsResponse] =
      await Promise.all([
        fetch("/package.json"),
        fetch("/AppContext.tsx"),
        fetch("/ui-components.txt"),
      ]);

    const packages = await packageResponse.text();
    const context = await contextResponse.text();
    const componentsList = await componentsResponse.text();

    // Convert to comma-separated list for backend
    const components = componentsList
      .split("\n")
      .filter(Boolean)
      .join(", ");

    return {
      query: text,
      context: context,
      packages: packages,
      components: components,
    };
  } catch (error) {
    console.error("Error reading files:", error);
    throw new Error(`Failed to prepare code message: ${error}`);
  }
};

export const constructChatStreamMessages = (
  messages: TypedMessage[]
) => {
  const messagesToSend = messages.map((message) => {
    return {
      role: message.type,
      content: message.content,
    };
  });

  return messagesToSend;
};
