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
import type { SubmitEvent } from "react";
import { recursivePrinter } from "../utils";

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

const ProjectCard = ({ project }: { project: Project }) => {
  return (
    <div className="flex flex-col gap-2 border p-4 rounded-md">
      {recursivePrinter(project)}
    </div>
  );
};

const ProjectList = () => {
  const { data: projects } = useQuery(getProjectsQueryOptions());
  const createProjectMutation = useCreateProjectMutation();

  const handleNewProjectClick = () => {
    console.log("New project clicked");
  };

  const handleCreateProjectSubmit = (
    e: SubmitEvent<HTMLFormElement>,
  ) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 m-4">
        {projects?.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </>
  );
};

export default ProjectList;
