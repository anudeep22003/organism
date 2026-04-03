import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SubmitEvent } from "react";
import { ProjectCard } from "./components/ProjectCard";
import { useCreateProject } from "../hooks/useCreateProject";
import { projectListOptions } from "../projects.queries";

const ProjectList = () => {
  const { data: projects } = useQuery(projectListOptions);
  const createProjectMutation = useCreateProject();

  const handleCreateProjectSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const projectName = formData.get("projectName") as string;
    createProjectMutation.mutate({ name: projectName });
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Projects</h1>
      <form
        onSubmit={handleCreateProjectSubmit}
        className="flex gap-2 mb-6 max-w-md"
      >
        <Input type="text" placeholder="Project name" name="projectName" />
        <Button type="submit">Create</Button>
      </form>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects?.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
};

export default ProjectList;
