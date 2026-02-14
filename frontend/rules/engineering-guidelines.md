# Frontend Engineering Guidelines

## Purpose

These rules optimize for:

- Fast iteration as a solo founder.
- High code quality for incoming contributors.
- Predictable architecture with low onboarding cost.

If a rule conflicts with shipping a critical fix, ship first and leave a short TODO with a follow-up issue.

## Core Principles

- Prefer feature boundaries over technical-layer boundaries.
- Keep state ownership explicit: server state vs UI state.
- Colocate by default.
- Avoid abstractions until the third real reuse (`rule of 3`).
- Optimize for readability and safe change, not cleverness.

## Directory and Ownership Rules

- New product work must live in `src/features/<feature-name>`.
- Each feature may contain only what it needs: `api/`, `model/`, `ui/`, `routing/`, `lib/`.
- Feature public API is exported from `src/features/<feature-name>/index.ts`.
- Cross-feature imports must use the feature public API, not deep internal paths.
- Existing legacy code under `src/pages/*` is treated as migration targets.

## Colocation Rules

- If a component is complex, it gets its own folder.
- Folder and component file names must match:
  - `ui/components/ProjectCard/ProjectCard.tsx`
  - `ui/components/ProjectCard/useProjectCard.ts`
  - `ui/components/ProjectCard/types.ts`
- Do not use `index.tsx` as the component file.
- Keep subcomponents and helper hooks inside the same component folder unless reused elsewhere.
- Promote code to feature-level only when reused by multiple component folders.

## TanStack Query Rules

- TanStack Query is the default source of truth for server state.
- Redux must not mirror server entities already in query cache.
- Every feature with server data must define a query key factory:
  - `<feature>.query-keys.ts`
- Query keys must be structured generic to specific.
- Queries, mutations, and keys should be colocated near the feature flows that use them.
- Use typed helpers for query config (`queryOptions`) to keep usage consistent.
- Mutation cache update strategy:
  - Use `setQueryData` for deterministic local updates.
  - Use `invalidateQueries` when backend performs non-trivial side effects.
- Components should not manually orchestrate scattered `refetch()` calls; prefer key-driven invalidation.

## Query Key Pattern

Use this shape consistently:

```ts
export const comicBuilderKeys = {
  all: ["comicBuilder"] as const,
  projects: () => [...comicBuilderKeys.all, "projects"] as const,
  project: (projectId: string) =>
    [...comicBuilderKeys.all, "project", projectId] as const,
  phase: (projectId: string, phase: string) =>
    [...comicBuilderKeys.project(projectId), "phase", phase] as const,
};
```

## Redux Rules

- Redux is for UI/app state only:
  - Current phase, local toggles, draft input, temporary wizard state.
- If state is used by one screen subtree, prefer local component state first.
- Do not store duplicated API loading/data/error state in Redux when TanStack Query already owns it.

## API Boundary Rules

- API modules handle transport and response mapping only.
- Keep backend DTO types separate from frontend domain types when shapes differ.
- Validate critical API responses at boundaries (e.g., Zod) where runtime safety matters.
- Keep side effects out of presentational components.

## Error Handling and Async UX

- All async user actions must have explicit loading and error states.
- Errors shown to users should be actionable where possible (retry, next step).
- Log errors with enough context for debugging.
- Avoid silent failures.

## Testing Expectations

- New critical workflows require tests:
  - Query/mutation behavior for key feature APIs.
  - At least one integration path for major user flows.
- Write tests for behavior, not internal implementation details.
- During migration, add tests on v2 paths before deleting v1 paths.

## Migration Strategy Rules

- Prefer staged migration (`v2 alongside v1`) for high-coupling modules.
- Keep overlap short; remove dead v1 code after parity is validated.
- Do not maintain dual architectures longer than necessary.

## Code Review and Change Discipline

- Keep PRs focused and small enough to review quickly.
- Document non-obvious architectural decisions in the PR description.
- If introducing a new pattern, add a short note to this file in the same PR.

## Naming and File Conventions

- Use clear, explicit names over abbreviations.
- Keep files cohesive; split files that become multi-responsibility.
- Prefer one exported component per component file.
- Default to named exports for utilities and hooks; use consistent style within each feature.
