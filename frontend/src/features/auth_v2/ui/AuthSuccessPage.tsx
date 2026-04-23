import AuthOutcomePage from "./AuthOutcomePage";

const AuthSuccessPage = () => {
  return (
    <AuthOutcomePage
      title="Authentication succeeded"
      description="OAuth returned successfully. Inspect the received query params below."
    />
  );
};

export default AuthSuccessPage;
