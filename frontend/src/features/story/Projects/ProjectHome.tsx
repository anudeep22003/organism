import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { useParams } from "react-router";
import { PROJECT_ENDPOINT } from "./constants";
import type { ProjectHomeType } from "./types";

const projectHomeQueryKeys = {
  all: ["project", "home"] as const,
  details: (projectId: string) =>
    [...projectHomeQueryKeys.all, projectId] as const,
};

// eslint-disable-next-line
const getProjectHomeDetailsQueryOptions = (projectId: string) => {
  return queryOptions({
    queryKey: projectHomeQueryKeys.details(projectId),
    queryFn: (projectId) =>
      httpClient.get<ProjectHomeType>(
        `${PROJECT_ENDPOINT}/${projectId}`,
      ),
  });
};

const ProjectHome = () => {
  const { projectId } = useParams();
  return <div>ProjectHome {projectId}</div>;
};

export default ProjectHome;
