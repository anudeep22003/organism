import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Link } from "react-router";
import { useDeleteStory } from "../hooks/useDeleteStory";
import type { StoryListEntryType } from "../types";

export const StoryCard = ({
  story,
  projectId,
}: {
  story: StoryListEntryType;
  projectId: string;
}) => {
  const deleteStoryMutation = useDeleteStory(projectId, story.id);

  const storyPreview =
    story.storyText?.slice(0, 120) || "Empty story — click to start writing";
  const hasContent = !!story.storyText;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {hasContent ? `Story ${story.id.slice(0, 8)}...` : "New Story"}
        </CardTitle>
        <CardDescription className="line-clamp-2">
          {storyPreview}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex gap-2">
        <Link to={`/story/${story.id}/create`}>
          <Button variant="outline" size="sm">
            {hasContent ? "Continue" : "Start Writing"}
          </Button>
        </Link>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => deleteStoryMutation.mutate()}
        >
          Delete
        </Button>
      </CardContent>
    </Card>
  );
};
