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
import { httpClient } from "@/lib/httpClient";

interface User {
  email: string;
  id: string;
  updatedAt: string;
}

interface LoginResponse {
  user?: User;
  statusCode: [
    "SUCCESS",
    "USER_NOT_FOUND",
    "INVALID_CREDENTIALS",
    "USER_ALREADY_EXISTS",
    "INTERNAL_ERROR"
  ];
}

const AuthPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const tabFromUrl = searchParams.get("tab") || "signin";
  const [activeTab, setActiveTab] = useState<string>(tabFromUrl);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSearchParams({ tab: value });
  };

  const handleSignIn = async (data: SignInFormData) => {
    console.log("Sign in:", data);
    try {
      const response = await httpClient.post<LoginResponse>(
        "/api/auth/signup",
        data
      );
      console.log("Login status", response);
      navigate("/");
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Login failed for unknown reasons. Please try again.";

      setError(errorMessage);
      console.log(error);
    }
  };

  const handleSignUp = async (data: SignUpFormData) => {
    console.log("Sign up:", data);
    try {
      const response = await httpClient.post<LoginResponse>(
        "/api/auth/signup",
        data
      );
      console.log("Login status", response);
      // navigate("/");
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Login failed for unknown reasons. Please try again.";

      setError(errorMessage);
      console.log(error);
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
