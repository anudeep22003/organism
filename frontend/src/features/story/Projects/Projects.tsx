import { Button } from "@/components/ui/button";

const Projects = () => {
  const handleNewProjectClick = () => {
    console.log("New project clicked");
  };
  return (
    <>
      <div>Projects</div>
      <Button onClick={handleNewProjectClick}>New Project</Button>
    </>
  );
};

export default Projects;
