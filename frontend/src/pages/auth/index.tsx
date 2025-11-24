import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
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
import { SignInForm } from "./components/SignInForm";
import { SignUpForm } from "./components/SignUpForm";
import type { SignInFormData, SignUpFormData } from "./types";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { useAuthContext } from "./context";
import useAuthEntry from "./hooks/useAuth";
import { authLogger } from "@/lib/logger";

interface User {
  email: string;
  id: string;
  updatedAt: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
}


const AuthPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { accessToken, setAccessToken  } = useAuthContext();
  const tabFromUrl = searchParams.get("tab") || "signin";
  const [activeTab, setActiveTab] = useState<string>(tabFromUrl);
  const { signIn, signUp } = useAuthEntry();

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSearchParams({ tab: value });
  };

  const handleSignIn = async (data: SignInFormData) => {
    authLogger.debug("New sign in attempt");
    authLogger.debug("Sign in:", data);
    authLogger.debug("Access token:", accessToken);
    try {
      const response = await signIn(data);
      authLogger.debug("Login status", response);
      setAccessToken(response.accessToken);
      // navigate("/");
    } catch (err) {
      const { status } = getAxiosErrorDetails(err);
      authLogger.error("Sign in failed:", err);
      if (status === 401) {
        navigate("/auth?tab=signup", {
          replace: true,
        });
      }
    }
  };

  const handleSignUp = async (data: SignUpFormData) => {
    authLogger.debug("Sign up:", data);
    try {
      const response = await signUp(data);
      authLogger.debug("Login status", response);
      setAccessToken(response.accessToken);
      // navigate("/");
    } catch (err) {
      const { status } = getAxiosErrorDetails(err);
      authLogger.error("Sign up failed:", err);
      if (status === 400) {
        navigate("/auth?tab=signin", {
          replace: true,
        });
      }
    }
  };

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
          <Tabs value={activeTab} onValueChange={handleTabChange}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="signin">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>
            <TabsContent value="signin" className="mt-6">
              <SignInForm onSubmit={handleSignIn} />
            </TabsContent>
            <TabsContent value="signup" className="mt-6">
              <SignUpForm onSubmit={handleSignUp} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuthPage;

// barrel exports
export { default as AuthProvider } from "./context";
