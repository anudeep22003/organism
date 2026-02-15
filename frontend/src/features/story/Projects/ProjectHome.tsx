import { httpClient } from "@/lib/httpClient";
import { queryOptions, useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { PROJECT_ENDPOINT } from "./constants";
import type { ProjectHomeType } from "./types";
import { recursivePrinter } from "../utils";

const projectHomeQueryKeys = {
  all: ["project", "home"] as const,
  details: (projectId: string) =>
    [...projectHomeQueryKeys.all, projectId] as const,
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

const ProjectHome = () => {
  const { projectId } = useParams();
  console.log("projectId", projectId);
  const { data: projectHome } = useQuery(
    getProjectHomeDetailsQueryOptions(projectId ?? ""),
  );
  return <div>{recursivePrinter(projectHome ?? {})}</div>;
};

export default ProjectHome;
