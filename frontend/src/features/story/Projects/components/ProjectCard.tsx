import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Link } from "react-router";
import type { ProjectListEntryType } from "../types";

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

export const ProjectCard = ({
  project,
}: {
  project: ProjectListEntryType;
}) => {
  return (
    <Link to={`/story/p/${project.id}`}>
      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
        <CardHeader>
          <CardTitle>{project.name ?? "Untitled Project"}</CardTitle>
          <CardDescription>
            {project.storyCount}{" "}
            {project.storyCount === 1 ? "story" : "stories"}
            {" · "}
            Updated {formatDate(project.updatedAt)}
          </CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
};
