import { Button } from "@/components/ui/button";
import {
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

type Props = {
  projectName: string;
  setProjectName: (name: string) => void;
  onSubmit: () => void;
  isCreating: boolean;
};

export const CreateProjectDialog = ({
  projectName,
  setProjectName,
  onSubmit,
  isCreating,
}: Props) => (
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
