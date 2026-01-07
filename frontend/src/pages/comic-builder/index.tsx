import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { CreateProjectDialog } from "./components/CreateProjectDialog";
import { EmptyState } from "./components/EmptyState";
import { ProjectGrid } from "./components/ProjectGrid";
import {
  createProject,
  fetchProjects,
  resetCreateStatus,
  selectCreateStatus,
  selectProjects,
  selectProjectsStatus,
} from "./projectsSlice";

const Projects = () => {
  const dispatch = useAppDispatch();
  const projects = useAppSelector(selectProjects);
  const status = useAppSelector(selectProjectsStatus);
  const createStatus = useAppSelector(selectCreateStatus);

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [projectName, setProjectName] = useState("");

  useEffect(() => {
    if (status === "idle") {
      dispatch(fetchProjects());
    }
  }, [dispatch, status]);

  useEffect(() => {
    if (createStatus === "succeeded") {
      setIsDialogOpen(false);
      setProjectName("");
      dispatch(resetCreateStatus());
    }
  }, [createStatus, dispatch]);

  const handleCreateProject = () => {
    dispatch(createProject({ name: projectName }));
  };

  if (status === "loading") {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-neutral-500">Loading projects...</p>
      </div>
    );
  }

  const isCreating = createStatus === "loading";

  return (
    <div className="mx-auto max-w-4xl p-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-medium text-neutral-900 dark:text-neutral-100">
          Projects
        </h1>
        {projects.length > 0 && (
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="size-4" />
                New Project
              </Button>
            </DialogTrigger>
            <CreateProjectDialog
              projectName={projectName}
              setProjectName={setProjectName}
              onSubmit={handleCreateProject}
              isCreating={isCreating}
            />
          </Dialog>
        )}
      </div>

      {projects.length === 0 ? (
        <EmptyState
          isDialogOpen={isDialogOpen}
          setIsDialogOpen={setIsDialogOpen}
          projectName={projectName}
          setProjectName={setProjectName}
          onSubmit={handleCreateProject}
          isCreating={isCreating}
        />
      ) : (
        <ProjectGrid projects={projects} />
      )}
    </div>
  );
};

export default Projects;
