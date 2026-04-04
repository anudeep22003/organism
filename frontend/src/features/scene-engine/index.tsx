import PromptInput from "./components/PromptInput";

export default function SceneEngine() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="w-full max-w-xl border border-border">
        <PromptInput onSend={(value) => console.log(value)} />
      </div>
    </div>
  );
}
