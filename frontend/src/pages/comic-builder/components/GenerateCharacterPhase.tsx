import { Button } from "@/components/ui/button";
import { httpClient } from "@/lib/httpClient";

const dummyApiCall = async () => {
  const response = await httpClient.get<{ message: string }>(
    "/api/comic-builder/phase/dummy"
  );
  console.log(response.message);
  return response;
};

export const dummyPrint = () => {
  console.log(
    "dummy print from dummyPrint function that was triggered by a socket event, yayyy"
  );
};

const GenerateCharacterPhase = () => {
  return (
    <div className="w-full max-w-4xl px-4 space-y-6">
      <h2 className="text-xl font-semibold text-black">
        Generate Characters
      </h2>
      <Button onClick={dummyApiCall}>Generate Characters</Button>
    </div>
  );
};

export default GenerateCharacterPhase;
