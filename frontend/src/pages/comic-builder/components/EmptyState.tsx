import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { Plus } from "lucide-react";
import { CreateProjectDialog } from "./CreateProjectDialog";

type Props = {
  isDialogOpen: boolean;
  setIsDialogOpen: (open: boolean) => void;
  projectName: string;
  setProjectName: (name: string) => void;
  onSubmit: () => void;
  isCreating: boolean;
};

export const EmptyState = ({
  isDialogOpen,
  setIsDialogOpen,
  projectName,
  setProjectName,
  onSubmit,
  isCreating,
}: Props) => (
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
      <CreateProjectDialog
        projectName={projectName}
        setProjectName={setProjectName}
        onSubmit={onSubmit}
        isCreating={isCreating}
      />
    </Dialog>
  </div>
);

