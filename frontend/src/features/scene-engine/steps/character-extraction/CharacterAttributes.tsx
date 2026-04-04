type CharacterAttributesProps = {
  character: Record<string, unknown>;
};

export function CharacterAttributes({ character }: CharacterAttributesProps) {
  return (
    <pre className="whitespace-pre-wrap text-[10px] text-muted-foreground">
      {JSON.stringify(character, null, 2)}
    </pre>
  );
}
