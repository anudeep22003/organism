export const authV2Keys = {
  all: ["auth_v2"] as const,
  me: () => [...authV2Keys.all, "me"] as const,
};
