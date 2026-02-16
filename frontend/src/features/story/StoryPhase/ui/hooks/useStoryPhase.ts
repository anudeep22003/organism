import { useCallback, useRef, useState } from "react";
import { httpClient } from "@/lib/httpClient";
import { PROJECT_ENDPOINT } from "../../api/story-phase.constants";
import type {
  PromptMessage,
  StoryStreamChunk,
} from "../../api/story-phase.types";

const PLACEHOLDER_STORY = `The old lighthouse keeper had not spoken to another soul in eleven years. Not out of spite or sorrow, but because the light demanded silence — a deep, reverential quiet that settled into his bones like salt into driftwood.

Each evening he climbed the spiral staircase, one hundred and forty-seven steps worn smooth by generations of careful feet. The lamp at the top was not electric. It had never been electric. It burned with something older, something that pulsed in rhythm with the tides.

"You understand," the light had told him on his first night, "that this is not a job. It is a conversation."

He had nodded, unsure what it meant. Now he knew. The light spoke in colors — amber for calm seas, deep violet before a storm, a pale trembling green when something ancient stirred beneath the waves. And he answered with his presence, his stillness, his willingness to watch.

The fishermen in the village below thought him mad. They left provisions at the base of the cliff every Tuesday — bread, cheese, dried fish, a bottle of wine — and retreated before he could descend. He always waited until their boats were specks on the horizon before collecting the basket.

Tonight the light burned a color he had never seen. Not quite red, not quite gold. Something between a warning and an invitation. He pressed his palm against the glass and felt it vibrate, a low hum that traveled up his arm and settled behind his eyes.

"Someone is coming," the light said. Not in words. In the way the shadows shifted on the wall, forming shapes that his mind assembled into meaning.

He looked out toward the sea. The horizon was dark, featureless, the sky and water merged into a single black canvas. But there — far out — a pinprick of answering light. Faint. Uncertain. Growing.

For the first time in eleven years, the keeper opened his mouth to speak. The words that came out were not his own. They were old words, salt-crusted and barnacled, dredged up from whatever deep place the lighthouse drew its power.

The approaching light flickered in response.

And the conversation, at last, became something more.`;

export function useStoryPhase(projectId: string) {
  const [messages, setMessages] = useState<PromptMessage[]>([]);
  const [storyText, setStoryText] = useState(PLACEHOLDER_STORY);
  const [isGenerating, setIsGenerating] = useState(false);
  const abortRef = useRef(false);

  const submitPrompt = useCallback(
    async (text: string) => {
      const newMessage: PromptMessage = {
        id: crypto.randomUUID(),
        text,
        timestamp: Date.now(),
      };

      const updatedMessages = [...messages, newMessage];
      setMessages(updatedMessages);
      setStoryText("");
      setIsGenerating(true);
      abortRef.current = false;

      try {
        const allInputTexts = updatedMessages.map((m) => m.text);
        const stream = httpClient.streamPost<StoryStreamChunk>(
          `${PROJECT_ENDPOINT}/${projectId}/story/generate`,
          { userInputText: allInputTexts },
        );

        for await (const chunk of stream) {
          if (abortRef.current) break;
          setStoryText((prev) => prev + chunk.text);
        }
      } catch (error) {
        console.error("Story generation failed:", error);
      } finally {
        setIsGenerating(false);
      }
    },
    [messages, projectId],
  );

  return {
    messages,
    storyText,
    isGenerating,
    submitPrompt,
  };
}
