import { Button } from "@/components/ui/button";
import { httpClient } from "@/lib/httpClient";
import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useParams } from "react-router";
import { PROJECT_ENDPOINT } from "./constants";
import type { ProjectHomeType, StoryListEntryType } from "./types";

const projectHomeQueryKeys = {
  all: ["project", "home"] as const,
  details: (projectId: string) =>
    [...projectHomeQueryKeys.all, projectId] as const,
  story: (projectId: string, storyId: string) =>
    [
      ...projectHomeQueryKeys.details(projectId),
      "story",
      storyId,
    ] as const,
};

const getProjectHomeDetailsQueryOptions = (projectId: string) => {
  return queryOptions({
    queryKey: projectHomeQueryKeys.details(projectId),
    queryFn: () =>
      httpClient.get<ProjectHomeType>(
        `${PROJECT_ENDPOINT}/${projectId}`,
      ),
  });
};

const useAddStoryMutation = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      httpClient.post<Record<string, unknown>>(
        `${PROJECT_ENDPOINT}/${projectId}/story`,
        {
          projectId,
        },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeQueryKeys.details(projectId),
      }),
  });
};

const useDeleteStoryMutation = (projectId: string, storyId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      httpClient.delete(
        `${PROJECT_ENDPOINT}/${projectId}/story/${storyId}`,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeQueryKeys.details(projectId),
      }),
  });
};

const StoryListEntry = ({ story }: { story: StoryListEntryType }) => {
  const deleteStoryMutation = useDeleteStoryMutation(
    story.projectId,
    story.id,
  );
  const handleDeleteStory = () => {
    deleteStoryMutation.mutate();
  };
  return (
    <div>
      {story.storyText ?? "No story text"}{" "}
      <Button onClick={handleDeleteStory}>Delete Story</Button>
    </div>
  );
};

const ProjectHome = () => {
  const { projectId } = useParams();
  console.log("projectId", projectId);
  const { data: projectHome } = useQuery(
    getProjectHomeDetailsQueryOptions(projectId ?? ""),
  );
  const addStoryMutation = useAddStoryMutation(projectId ?? "");
  const handleAddStory = () => {
    addStoryMutation.mutate();
  };
  if (!projectHome) {
    return <div>Project not found</div>;
  }
  return (
    <div className="flex flex-col">
      <h1 className="text-2xl font-bold">Project Home</h1>
      <pre>{JSON.stringify(projectHome, null, 2)}</pre>
      {projectHome.stories?.map((story) => (
        <StoryListEntry key={story.id} story={story} />
      ))}
      <Button onClick={handleAddStory}>Add Story</Button>
    </div>
  );
};

export default ProjectHome;
