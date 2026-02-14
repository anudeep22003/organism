// TODO remove
/* eslint-disable react-refresh/only-export-components */
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { httpClient } from "@/lib/httpClient";
import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

export const projectKeys = {
  all: ["projects"] as const,
};

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

export type Project = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
};

export type CreateProject = {
  name: string;
};

export const getProjectsQueryOptions = () =>
  queryOptions({
    queryKey: projectKeys.all,
    queryFn: () => httpClient.get<Project[]>(PROJECT_ENDPOINT),
    staleTime: Infinity,
  });

const useCreateProjectMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProject) =>
      httpClient.post<Project>(PROJECT_ENDPOINT, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: projectKeys.all }),
  });
};

const Projects = () => {
  const { data: projects } = useQuery(getProjectsQueryOptions());
  const createProjectMutation = useCreateProjectMutation();

  const handleNewProjectClick = () => {
    console.log("New project clicked");
  };

  const handleCreateProjectSubmit = (
    e: React.FormEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    const projectName = formData.get("projectName") as string;
    createProjectMutation.mutate({ name: projectName });
  };

  return (
    <>
      <div>Projects</div>
      <form onSubmit={handleCreateProjectSubmit}>
        <Input
          type="text"
          placeholder="Project name"
          name="projectName"
        />
        <Button type="submit">Create Project</Button>
      </form>
      <Button onClick={handleNewProjectClick}>New Project</Button>`
      {JSON.stringify(projects)}`
    </>
  );
};

export default Projects;
