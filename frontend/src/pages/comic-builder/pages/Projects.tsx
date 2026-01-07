import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect } from "react";
import {
  fetchProjects,
  selectProjects,
  selectProjectsStatus,
} from "../projectsSlice";

const Projects = () => {
  const dispatch = useAppDispatch();
  const projects = useAppSelector(selectProjects);
  const status = useAppSelector(selectProjectsStatus);

  useEffect(() => {
    if (status === "idle") {
      dispatch(fetchProjects());
    }
  }, [dispatch, status]);

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  console.log("projects:", projects);
  return <div>Projects</div>;
};

export default Projects;
