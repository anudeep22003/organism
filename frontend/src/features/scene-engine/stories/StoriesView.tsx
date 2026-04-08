import { myProjectOptions } from "@/features/story/projects/projects.queries";
import type { StoryListEntryType } from "@/features/story/shared/story.types";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router";
import { Skeleton } from "../components/Skeleton";
import { NewStoryModal } from "./NewStoryModal";

function StoryGrid({
  stories,
  isEditMode,
  onCardClick,
}: {
  stories: StoryListEntryType[];
  isEditMode: boolean;
  onCardClick: (story: StoryListEntryType) => void;
}) {
  const navigate = useNavigate();

  if (stories.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center border border-border bg-muted/20">
        <span className="text-xs text-muted-foreground">
          No stories yet. Create your first one.
        </span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 items-start gap-2 md:grid-cols-3">
      {stories.map((story) => (
        <div
          key={story.id}
          onClick={() =>
            isEditMode
              ? onCardClick(story)
              : void navigate(`/story/${story.id}`)
          }
          className={`flex cursor-pointer flex-col gap-1 border border-border p-3 transition-colors ${
            isEditMode
              ? "bg-muted/30 hover:bg-muted/50 ring-1 ring-border"
              : "bg-muted/20 hover:bg-muted/40"
          }`}
        >
          <span className="line-clamp-1 text-xs font-medium text-foreground">
            {story.name ?? "Untitled story"}
          </span>
          {story.description && (
            <span className="text-[10px] text-muted-foreground">
              {story.description}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

function StoriesGridSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-32" />
      ))}
    </div>
  );
}

export default function StoriesView() {
  const [showModal, setShowModal] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingStory, setEditingStory] = useState<StoryListEntryType | null>(null);
  const { data: myProject, isLoading } = useQuery(myProjectOptions);

  const handleDismiss = () => {
    setShowModal(false);
    setEditingStory(null);
    setIsEditMode(false);
  };

  const handleCardClick = (story: StoryListEntryType) => {
    setEditingStory(story);
  };

  return (
    <div className="relative flex min-h-0 flex-1 flex-col gap-4 p-6">
      {(showModal || editingStory) && myProject && (
        <NewStoryModal
          projectId={myProject.id}
          story={editingStory ?? undefined}
          onDismiss={handleDismiss}
        />
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Stories</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditMode((prev) => !prev)}
            className={`border border-border px-3 py-1.5 text-xs transition-colors ${
              isEditMode
                ? "border-foreground text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {isEditMode ? "Done" : "Edit"}
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="bg-foreground px-3 py-1.5 text-xs text-background hover:bg-foreground/80"
          >
            New Story
          </button>
        </div>
      </div>

      {isLoading ? (
        <StoriesGridSkeleton />
      ) : (
        <StoryGrid
          stories={myProject?.stories ?? []}
          isEditMode={isEditMode}
          onCardClick={handleCardClick}
        />
      )}
    </div>
  );
}
