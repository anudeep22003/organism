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
import { PROJECT_ENDPOINT } from "./constants";
import type { ProjectListEntryType } from "./types";
import { Link } from "react-router";

export const projectKeys = {
  all: ["projects"] as const,
};

export type CreateProject = {
  name: string;
};

export const getProjectsQueryOptions = () =>
  queryOptions({
    queryKey: projectKeys.all,
    queryFn: () =>
      httpClient.get<ProjectListEntryType[]>(PROJECT_ENDPOINT),
    staleTime: Infinity,
  });

const useCreateProjectMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProject) =>
      httpClient.post<ProjectListEntryType>(PROJECT_ENDPOINT, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: projectKeys.all }),
  });
};

const ProjectCard = ({
  project,
}: {
  project: ProjectListEntryType;
}) => {
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
          <div className="flex flex-col gap-2">
            <ProjectCard key={project.id} project={project} />
            <Link to={`/story/${project.id}`}>View Project</Link>
          </div>
        ))}
      </div>
    </>
  );
};

export default ProjectList;
