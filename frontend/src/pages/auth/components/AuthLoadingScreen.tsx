const AuthLoadingScreen = () => {
  return (
    <div
      className="min-h-screen flex items-center justify-center bg-black"
      role="status"
      aria-live="polite"
      aria-label="Authenticating"
    >
      <div className="flex flex-col items-center gap-6">
        {/* Spinner */}
        <div className="relative">
          <div className="w-16 h-16 border-4 border-gray-800 border-t-white rounded-full animate-spin" />
          <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-gray-600 rounded-full animate-spin animation-delay-150" />
        </div>

        {/* Loading text with fade animation */}
        <div className="flex flex-col items-center gap-2">
          <p className="text-white text-lg font-medium animate-pulse">
            Authenticating
          </p>
          <p className="text-gray-400 text-sm">
            Please wait a moment...
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthLoadingScreen;
