import { myProjectOptions } from "@/features/story/projects/projects.queries";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router";
import { Skeleton } from "../components/Skeleton";
import { NewStoryModal } from "./NewStoryModal";

function StoryGrid({
  stories,
}: {
  stories: { id: string; storyText: string; userInputText: string }[];
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
    <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
      {stories.map((story) => (
        <div
          key={story.id}
          onClick={() => void navigate(`/story/${story.id}`)}
          className="flex h-32 cursor-pointer flex-col items-start justify-end border border-border bg-muted/20 p-3 hover:bg-muted/40"
        >
          <span className="line-clamp-2 text-xs text-muted-foreground">
            {story.userInputText || story.storyText || "Untitled story"}
          </span>
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
  const { data: myProject, isLoading } = useQuery(myProjectOptions);

  return (
    <div className="relative flex min-h-0 flex-1 flex-col gap-4 p-6">
      {showModal && myProject && (
        <NewStoryModal
          projectId={myProject.id}
          onDismiss={() => setShowModal(false)}
        />
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Stories</span>
        <button
          onClick={() => setShowModal(true)}
          className="bg-foreground px-3 py-1.5 text-xs text-background hover:bg-foreground/80"
        >
          New Story
        </button>
      </div>

      {isLoading ? (
        <StoriesGridSkeleton />
      ) : (
        <StoryGrid stories={myProject?.stories ?? []} />
      )}
    </div>
  );
}
