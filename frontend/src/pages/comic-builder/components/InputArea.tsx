import { IconPlus } from "@tabler/icons-react";
import { ArrowUpIcon } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import { useState } from "react";

type InputAreaProps = {
  onSubmit: (draft: string) => void;
};

const InputArea = ({ onSubmit }: InputAreaProps) => {
  const [draft, setDraft] = useState("");

  const handleSubmitClick = () => {
    onSubmit(draft);
  };

  return (
    <div className="grid w-full max-w-2/3 gap-6">
      <InputGroup>
        <InputGroupTextarea
          placeholder="Ask, Search or Chat..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              (e.metaKey || e.ctrlKey) &&
              draft.trim() !== ""
            ) {
              e.preventDefault();
              handleSubmitClick();
            }
          }}
        />
        <InputGroupAddon align="block-end">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <InputGroupButton
                variant="outline"
                className="rounded-full"
                size="icon-xs"
                onClick={() => console.log("add attachment click")}
              >
                <IconPlus />
              </InputGroupButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              side="top"
              align="start"
              className="[--radius:0.95rem]"
            >
              <DropdownMenuItem>Picture</DropdownMenuItem>
              <DropdownMenuItem>Text</DropdownMenuItem>
              <DropdownMenuItem>Audio</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <InputGroupButton
            variant="default"
            className="rounded-full ml-auto"
            size="icon-xs"
            onClick={handleSubmitClick}
          >
            <ArrowUpIcon />
            <span className="sr-only">Send</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    </div>
  );
};

export default InputArea;
