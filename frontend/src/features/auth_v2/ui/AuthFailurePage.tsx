import AuthOutcomePage from "./AuthOutcomePage";

const AuthFailurePage = () => {
  return (
    <AuthOutcomePage
      title="Authentication failed"
      description="OAuth returned an error. Inspect the received query params below."
    />
  );
};

export default AuthFailurePage;
