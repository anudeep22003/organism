import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
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
            <CreateProjectDialogContent
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

type CreateProjectDialogContentProps = {
  projectName: string;
  setProjectName: (name: string) => void;
  onSubmit: () => void;
  isCreating: boolean;
};

const CreateProjectDialogContent = ({
  projectName,
  setProjectName,
  onSubmit,
  isCreating,
}: CreateProjectDialogContentProps) => (
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create New Project</DialogTitle>
      <DialogDescription>
        Give your project a name to get started.
      </DialogDescription>
    </DialogHeader>
    <div className="py-4">
      <Textarea
        placeholder="e.g. My first comic, Untitled adventure, Chapter 1..."
        value={projectName}
        onChange={(e) => setProjectName(e.target.value)}
        className="min-h-24 resize-none"
      />
    </div>
    <DialogFooter>
      <Button onClick={onSubmit} disabled={isCreating}>
        {isCreating ? "Creating..." : "Create Project"}
      </Button>
    </DialogFooter>
  </DialogContent>
);

type EmptyStateProps = {
  isDialogOpen: boolean;
  setIsDialogOpen: (open: boolean) => void;
  projectName: string;
  setProjectName: (name: string) => void;
  onSubmit: () => void;
  isCreating: boolean;
};

const EmptyState = ({
  isDialogOpen,
  setIsDialogOpen,
  projectName,
  setProjectName,
  onSubmit,
  isCreating,
}: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center py-24">
    <div className="mb-6 rounded-full bg-neutral-100 p-4 dark:bg-neutral-800">
      <Plus className="size-8 text-neutral-400" />
    </div>
    <h2 className="mb-2 text-lg font-medium text-neutral-900 dark:text-neutral-100">
      No projects yet
    </h2>
    <p className="mb-6 text-sm text-neutral-500">
      Create your first project to get started.
    </p>
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" />
          Create Project
        </Button>
      </DialogTrigger>
      <CreateProjectDialogContent
        projectName={projectName}
        setProjectName={setProjectName}
        onSubmit={onSubmit}
        isCreating={isCreating}
      />
    </Dialog>
  </div>
);

type Project = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
};

type ProjectGridProps = {
  projects: Project[];
};

const ProjectGrid = ({ projects }: ProjectGridProps) => (
  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {projects.map((project) => (
      <ProjectCard key={project.id} project={project} />
    ))}
  </div>
);

type ProjectCardProps = {
  project: Project;
};

const ProjectCard = ({ project }: ProjectCardProps) => {
  const displayName = project.name || "Untitled";
  const createdDate = new Date(project.createdAt).toLocaleDateString();

  return (
    <Card className="cursor-pointer transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">
          {displayName}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">
          Created {createdDate}
        </p>
      </CardContent>
    </Card>
  );
};

export default Projects;
