import type { Project } from "../types/project";
import { ProjectCard } from "./ProjectCard";

type Props = {
  projects: Project[];
};

export const ProjectGrid = ({ projects }: Props) => (
  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {projects.map((project) => (
      <ProjectCard key={project.id} project={project} />
    ))}
  </div>
);

