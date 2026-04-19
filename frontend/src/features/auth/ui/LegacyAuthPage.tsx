import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { useCallback, useEffect, useState } from "react";
import {
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router";
import {
  AUTH_QUERY_PARAMS,
  AUTH_ROUTES,
  AUTH_TABS,
  HTTP_STATUS,
  type AuthTab,
} from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import {
  buildAuthRoute,
  getAuthTabFromSearchParams,
  getRedirectFromSearchParams,
} from "../routing/auth-redirect";
import { SignInForm } from "./components/SignInForm";
import { SignUpForm } from "./components/SignUpForm";

const LegacyAuthPage = () => {
  const [, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, signUp } = useAuth();

  const tabFromUrl = getAuthTabFromSearchParams(location.search);
  const redirectTarget = getRedirectFromSearchParams(location.search);
  const [activeTab, setActiveTab] = useState<AuthTab>(tabFromUrl);

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  const handleTabChange = useCallback(
    (tab: AuthTab) => {
      setActiveTab(tab);

      const nextSearchParams = new URLSearchParams({
        [AUTH_QUERY_PARAMS.TAB]: tab,
      });

      if (redirectTarget) {
        nextSearchParams.set(
          AUTH_QUERY_PARAMS.REDIRECT,
          redirectTarget
        );
      }

      setSearchParams(nextSearchParams);
    },
    [redirectTarget, setSearchParams]
  );

  const onSignIn = useCallback(
    async (credentials: { email: string; password: string }) => {
      try {
        await signIn(credentials);
        navigate(redirectTarget ?? AUTH_ROUTES.HOME_FALLBACK, {
          replace: true,
        });
      } catch (err) {
        const { status } = getAxiosErrorDetails(err);
        authLogger.error("Sign in failed:", err);
        if (status === HTTP_STATUS.UNAUTHORIZED) {
          navigate(
            buildAuthRoute({
              tab: AUTH_TABS.SIGNUP,
              redirectTo: redirectTarget,
            }),
            {
              replace: true,
            }
          );
        }
      }
    },
    [navigate, redirectTarget, signIn]
  );

  const onSignUp = useCallback(
    async (credentials: {
      fullName: string;
      email: string;
      password: string;
      acceptTerms: boolean;
    }) => {
      try {
        await signUp(credentials);
        navigate(redirectTarget ?? AUTH_ROUTES.HOME_FALLBACK, {
          replace: true,
        });
      } catch (err) {
        const { status } = getAxiosErrorDetails(err);
        authLogger.error("Sign up failed:", err);
        if (status === HTTP_STATUS.BAD_REQUEST) {
          navigate(
            buildAuthRoute({
              tab: AUTH_TABS.SIGNIN,
              redirectTo: redirectTarget,
            }),
            {
              replace: true,
            }
          );
        }
      }
    },
    [navigate, redirectTarget, signUp]
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Welcome
          </CardTitle>
          <CardDescription className="text-center">
            Sign in to your account or create a new one
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={(tab) => handleTabChange(tab as AuthTab)}
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value={AUTH_TABS.SIGNIN}>Sign In</TabsTrigger>
              <TabsTrigger value={AUTH_TABS.SIGNUP}>Sign Up</TabsTrigger>
            </TabsList>
            <TabsContent value={AUTH_TABS.SIGNIN} className="mt-6">
              <SignInForm onSubmit={onSignIn} />
            </TabsContent>
            <TabsContent value={AUTH_TABS.SIGNUP} className="mt-6">
              <SignUpForm onSubmit={onSignUp} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default LegacyAuthPage;
