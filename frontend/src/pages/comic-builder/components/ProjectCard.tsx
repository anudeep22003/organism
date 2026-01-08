import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Link } from "react-router";
import type { Project } from "../types";

type Props = {
  project: Project;
};

export const ProjectCard = ({ project }: Props) => {
  const displayName = project.name || "Untitled";
  const createdDate = new Date(project.createdAt).toLocaleDateString();

  return (
    <Link to={`/${project.id}`}>
      <Card className="cursor-pointer transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{displayName}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-neutral-500">Created {createdDate}</p>
        </CardContent>
      </Card>
    </Link>
  );
};
