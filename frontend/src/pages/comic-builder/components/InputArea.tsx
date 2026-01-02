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

type InputAreaProps = {
  onSendClick: () => void;
  setInputText: (value: string) => void;
  inputText: string;
};

const InputArea = ({
  onSendClick,
  setInputText,
  inputText,
}: InputAreaProps) => {
  return (
    <div className="grid w-full max-w-2/3 gap-6">
      <InputGroup>
        <InputGroupTextarea
          placeholder="Ask, Search or Chat..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              (e.metaKey || e.ctrlKey) &&
              inputText.trim() !== ""
            ) {
              e.preventDefault();
              onSendClick();
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
            onClick={onSendClick}
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
