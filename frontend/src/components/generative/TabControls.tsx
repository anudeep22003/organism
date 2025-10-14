import {
  useMessageStore,
} from "@/store/useMessageStore";

export const TabControls = () => {
  const activeTab = useMessageStore((state) => state.activeTab);


  if (activeTab === "writer") {
    return (
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Writer output ready for review.
        </p>
      </div>
    );
  }

  return null;
};
