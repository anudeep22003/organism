import {
  useMessageStore,
  useAvailableActors,
} from "@/store/useMessageStore";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { TabControls } from "./generative/TabControls";
import { TabLabel } from "./generative/TabLabel";
import type { Actor } from "@/socket/envelopeType";
import { ActorContent } from "./generative/ActorContent";

const GenerativeHeader = () => {
  return (
    <div className="p-4 border-b border-border flex justify-between items-center">
      <h2 className="text-lg font-medium">Generated Output</h2>
    </div>
  );
};

const EmptyState = () => {
  return (
    <div className="flex flex-col h-full bg-background">
      <GenerativeHeader />
      <div className="flex-1 flex items-center justify-center p-4">
        <p className="text-muted-foreground text-sm">
          No generated content yet. Use the Code or Write buttons to
          start.
        </p>
      </div>
    </div>
  );
};

export const GenerativeArea = () => {
  const allMessages = useMessageStore((state) => state.allMessages);

  const activeTab = useMessageStore((state) => state.activeTab);
  const setActiveTab = useMessageStore((state) => state.setActiveTab);
  const streamingActors = useMessageStore(
    (state) => state.streamingActors
  );
  const availableTabs = Array.from(useAvailableActors());

  const handleTabChange = (value: string) => {
    setActiveTab(value as Actor, true);
  };

  const currentTab = activeTab || availableTabs[0] || "coder";

  if (availableTabs.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* <GenerativeHeader /> */}

      {/* Sticky TabsList */}
      <div className="sticky top-0 z-10 bg-background border-b border-border px-4 pt-2 pb-2">
        <Tabs
          value={currentTab}
          onValueChange={handleTabChange}
          className="w-full"
        >
          <TabsList className="w-fit">
            {availableTabs.map((actor) => (
              <TabsTrigger key={actor} value={actor}>
                <TabLabel
                  actor={actor}
                  isStreaming={streamingActors.has(actor)}
                />
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto">
        <Tabs
          value={currentTab}
          onValueChange={handleTabChange}
          className="h-full"
        >
          {availableTabs.map((actor) => (
            <TabsContent
              key={actor}
              value={actor}
              className="h-full mt-0"
            >
              <ActorContent type={actor} allMessages={allMessages} />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      <div className="p-4 border-t border-border">
        <TabControls />
      </div>
    </div>
  );
};
