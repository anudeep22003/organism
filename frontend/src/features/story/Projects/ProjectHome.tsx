import { Button } from "@/components/ui/button";
import { Link, useParams } from "react-router";
import { StoryCard } from "./components/StoryCard";
import { useAddStory } from "./hooks/useAddStory";
import { useProjectHome } from "./hooks/useProjectHome";

const ProjectHome = () => {
  const { projectId } = useParams();
  const { data: projectHome } = useProjectHome(projectId ?? "");
  const addStoryMutation = useAddStory(projectId ?? "");

  if (!projectHome) {
    return <div className="p-6">Project not found</div>;
  }

  return (
    <div className="p-6">
      <Link
        to="/story"

        className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block"
      >
        &larr; All Projects
      </Link>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          {projectHome.name ?? "Untitled Project"}
        </h1>
        <p className="text-muted-foreground text-sm">
          {projectHome.stories?.length ?? 0}{" "}
          {projectHome.stories?.length === 1 ? "story" : "stories"}
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-6">
        {projectHome.stories?.map((story) => (
          <StoryCard
            key={story.id}
            story={story}
            projectId={projectId ?? ""}
          />
        ))}
      </div>
      <Button onClick={() => addStoryMutation.mutate()}>Add Story</Button>
    </div>
  );
};

export default ProjectHome;
