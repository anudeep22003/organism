import { useCreateStory } from "@/features/story/projects/hooks/useCreateStory";
import { useState } from "react";
import { useNavigate } from "react-router";

type RadioGroupProps = {
  options: string[];
  value: string;
  onChange: (v: string) => void;
};

function RadioGroup({ options, value, onChange }: RadioGroupProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {options.map((opt) => (
        <label key={opt} className="flex cursor-pointer items-center gap-2">
          <div
            onClick={() => onChange(opt)}
            className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center border border-border ${value === opt ? "bg-foreground" : "bg-background"}`}
          >
            {value === opt && <div className="h-1.5 w-1.5 bg-background" />}
          </div>
          <span className="text-xs text-foreground">{opt}</span>
        </label>
      ))}
    </div>
  );
}

type MultiSelectProps = {
  options: string[];
  value: string[];
  onChange: (v: string[]) => void;
};

function MultiSelect({ options, value, onChange }: MultiSelectProps) {
  const toggle = (opt: string) =>
    onChange(
      value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt],
    );

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`border px-2.5 py-1 text-xs transition-colors ${value.includes(opt) ? "border-foreground bg-foreground text-background" : "border-border text-muted-foreground hover:bg-muted/40"}`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2 border-b border-border pb-4">
      <span className="text-xs font-medium text-foreground">{label}</span>
      {children}
    </div>
  );
}

type NewStoryModalProps = {
  projectId: string;
  onDismiss: () => void;
};

export function NewStoryModal({ projectId, onDismiss }: NewStoryModalProps) {
  const navigate = useNavigate();
  const createStory = useCreateStory();

  const [about, setAbout] = useState("");
  const [hasBackdrop, setHasBackdrop] = useState("");
  const [backdrop, setBackdrop] = useState("");
  const [tone, setTone] = useState("");
  const [comicStyle, setComicStyle] = useState("");
  const [forSomeone, setForSomeone] = useState("");
  const [relationship, setRelationship] = useState("");
  const [feeling, setFeeling] = useState<string[]>([]);

  const handleCreate = () => {
    createStory.mutate(
      {
        projectId,
        meta: {
          about,
          tone,
          comicStyle,
          hasBackdrop,
          backdrop,
          forSomeone,
          relationship,
          feeling,
        },
      },
      {
        onSuccess: (story) => {
          void navigate(`/story/${story.id}`);
        },
      },
    );
  };

  return (
    <div className="absolute inset-0 z-20 flex flex-col bg-background">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-6 py-3">
        <span className="text-sm font-medium">New Story</span>
        <button
          onClick={onDismiss}
          className="bg-foreground px-2 py-1 text-xs text-background hover:bg-foreground/80"
        >
          ✕
        </button>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-6 py-4">
        <Field label="What is the story about?">
          <textarea
            value={about}
            onChange={(e) => setAbout(e.target.value)}
            placeholder="Describe your story..."
            rows={3}
            className="w-full resize-none border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
          />
        </Field>

        <Field label="Does the story have a backdrop?">
          <RadioGroup
            options={["Yes", "No"]}
            value={hasBackdrop}
            onChange={setHasBackdrop}
          />
          {hasBackdrop === "Yes" && (
            <input
              type="text"
              value={backdrop}
              onChange={(e) => setBackdrop(e.target.value)}
              placeholder="e.g. 1940s London, 2050 on the moon..."
              className="mt-1 w-full border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
            />
          )}
        </Field>

        <Field label="What tone are you going for?">
          <RadioGroup
            options={["Happy-go-lucky", "Dark and gritty", "Emotional"]}
            value={tone}
            onChange={setTone}
          />
        </Field>

        <Field label="What comic style do you like?">
          <MultiSelect
            options={[
              "Western",
              "Cartoon",
              "Manga",
              "Chinese doujin",
              "Korean manhwa",
            ]}
            value={comicStyle ? [comicStyle] : []}
            onChange={(v) => setComicStyle(v[v.length - 1] ?? "")}
          />
        </Field>

        <Field label="Are you making this for someone?">
          <RadioGroup
            options={["Yes", "No"]}
            value={forSomeone}
            onChange={setForSomeone}
          />
          {forSomeone === "Yes" && (
            <div className="mt-2 flex flex-col gap-3">
              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] text-muted-foreground">
                  Your relationship with them
                </span>
                <input
                  type="text"
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                  placeholder="e.g. best friend, partner, parent..."
                  className="w-full border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] text-muted-foreground">
                  What do you want them to feel? (select all that apply)
                </span>
                <MultiSelect
                  options={[
                    "Loved",
                    "Inspired",
                    "Nostalgic",
                    "Amused",
                    "Moved",
                    "Seen",
                  ]}
                  value={feeling}
                  onChange={setFeeling}
                />
              </div>
            </div>
          )}
        </Field>
      </div>

      <div className="flex shrink-0 justify-end border-t border-border px-6 py-3">
        <button
          onClick={handleCreate}
          disabled={!about.trim() || createStory.isPending}
          className="bg-foreground px-4 py-1.5 text-xs text-background hover:bg-foreground/80 disabled:opacity-50"
        >
          {createStory.isPending ? "Creating…" : "Create Story"}
        </button>
      </div>
    </div>
  );
}
