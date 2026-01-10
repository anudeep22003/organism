import { Button } from "@/components/ui/button";
import { httpClient } from "@/lib/httpClient";
import { useParams } from "react-router";

const ExtractCharactersPhase = () => {
  const { projectId } = useParams<{ projectId: string }>();
  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  const handleExtractCharactersClick = async () => {
    console.log("Extract Characters for project", projectId);
    const response = await httpClient.get<null>(
      `/api/comic-builder/phase/extract-characters/${projectId}`
    );
    if (!response) {
      console.error("Failed to extract characters");
      return;
    }
    console.log("Characters extracted successfully", response);
  };

  return (
    <>
      <Button onClick={handleExtractCharactersClick}>
        Extract Characters
      </Button>
    </>
  );
};

export default ExtractCharactersPhase;
