import { Link } from "react-router";
import { AUTH_V2_ROUTES } from "../api/auth.constants";
import AuthOutcomePage from "./AuthOutcomePage";

const AuthFailurePage = () => {
  return (
    <AuthOutcomePage
      title="Sign in failed"
      description="We could not complete the Google sign-in flow. Please try again."
      footer={
        <div className="flex items-center gap-3">
          <Link
            to={AUTH_V2_ROUTES.ROOT}
            className="inline-flex items-center justify-center border border-zinc-300 bg-white px-3 py-2 text-sm text-black transition-colors hover:bg-zinc-50"
          >
            Back to sign in
          </Link>
        </div>
      }
    >
      <div className="border border-border bg-background/80 px-4 py-3 text-xs text-muted-foreground">
        If this keeps happening, the backend callback or your session cookies
        are not being issued as expected.
      </div>
    </AuthOutcomePage>
  );
};

export default AuthFailurePage;
