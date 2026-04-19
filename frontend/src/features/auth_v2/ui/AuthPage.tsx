import { BACKEND_URL } from "@/constants";
import { AUTH_V2_SERVICE_ENDPOINTS } from "../api/auth.constants";

const GoogleLogo = () => {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 18 18"
      className="h-[18px] w-[18px]"
    >
      <path
        fill="#4285F4"
        d="M17.64 9.2045c0-.638-.0573-1.2518-.1636-1.8409H9v3.4818h4.8436c-.2086 1.125-.8427 2.0782-1.796 2.7164v2.2582h2.9087c1.7018-1.5664 2.6837-3.874 2.6837-6.6155z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.4673-.8064 5.9564-2.1791l-2.9087-2.2582c-.8064.54-1.8368.8591-3.0477.8591-2.3455 0-4.3282-1.5845-5.0364-3.7127H.9573v2.3327C2.4382 15.9836 5.4818 18 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.9636 10.7091C3.7837 10.1691 3.6818 9.5923 3.6818 9s.1019-1.1691.2818-1.7091V4.9582H.9573C.3477 6.1736 0 7.5477 0 9s.3477 2.8264.9573 4.0418l3.0063-2.3327z"
      />
      <path
        fill="#EA4335"
        d="M9 3.5782c1.3214 0 2.5077.4541 3.44 1.3459l2.5813-2.5814C13.4632.8918 11.426 0 9 0 5.4818 0 2.4382 2.0164.9573 4.9582l3.0063 2.3327C4.6718 5.1627 6.6545 3.5782 9 3.5782z"
      />
    </svg>
  );
};

const AuthPage = () => {
  const handleGoogleSignIn = () => {
    window.location.assign(
      `${BACKEND_URL}${AUTH_V2_SERVICE_ENDPOINTS.GOOGLE_LOGIN}`
    );
  };

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.16),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.18),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.14),transparent_28%),linear-gradient(180deg,rgba(250,250,250,0.95),rgba(244,244,245,0.92))] dark:bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.18),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.14),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.12),transparent_28%),linear-gradient(180deg,rgba(10,10,10,0.98),rgba(24,24,27,0.96))]" />
      </div>

      <div className="relative flex shrink-0 items-center border-b border-border bg-background/70 px-4 py-1.5 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
          <div className="h-2.5 w-px bg-border" />
          <span className="text-[10px] text-foreground">Sign in</span>
        </div>
      </div>

      <div className="relative flex min-h-0 flex-1 items-center justify-center p-4">
        <div className="flex w-full max-w-md flex-col border border-border bg-background/72 shadow-[0_24px_80px_rgba(0,0,0,0.06)] backdrop-blur-md dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
          <div className="flex flex-col gap-6 px-4 py-8 sm:px-6">
            <div className="space-y-2">
              <h1 className="text-base text-foreground">
                Identify yourself
              </h1>
              <p className="text-xs text-muted-foreground">
                Sign in with Google to continue.
              </p>
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              className="grid grid-cols-[20px_1fr_20px] items-center gap-3 border border-zinc-300 bg-white px-3 py-2.5 text-sm text-black transition-colors hover:bg-zinc-50"
            >
              <GoogleLogo />
              <span className="text-center font-medium">
                Sign in with Google
              </span>
              <span aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
