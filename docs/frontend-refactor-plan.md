# Frontend Refactor Kickoff

## Goals
- Modularize layout, routing, and provider wiring so features can evolve independently.
- Centralize API access patterns and data fetching with React Query to reduce duplicated fetch logic.
- Improve state boundaries (auth, navigation, domain data) and align them with backend capabilities.
- Establish consistent design primitives (layout, typography, feedback components) using MUI theming.

## Initial Changes (Completed)
- Extracted top-level layout concerns (top bar, sidebar, routes) into `src/app/` for clearer boundaries.
- Split the navigation menu (`AuthenticatedTopBarMenu`) and `TopBar` into dedicated components for reuse.
- Created explicit authenticated/unauthenticated layouts to prepare for route guards and skeleton loading states.
- Centralized route definitions in `app/routes/AppRoutes.tsx` to simplify future migrations to data routers.

## Next Iterations
1. **Data Access Layer**
   - Introduce a typed HTTP client (Axios or Fetch wrapper) with interceptors and error normalization.
   - Migrate `services/apiClient.ts` consumers to React Query hooks, co-locating caching keys and optimistic updates.
2. **State Management**
   - Replace ad-hoc context usage where Redux Toolkit or React Query can provide derived state.
   - Define permission/feature flag helpers in a shared `lib/auth` package.
3. **Routing & Layouts**
   - Move to file-based or config-driven routing (React Router data APIs), including error boundaries and loaders.
   - Add layout-level suspense states and skeletons for key admin sections.
4. **UI/UX Consistency**
   - Document design tokens, spacing, and typographic scale; enforce via shared theme utilities.
   - Audit forms to standardize validation/error messaging via `react-hook-form` resolvers.
5. **Testing Strategy**
   - Reinstate unit/integration tests for critical flows (auth transitions, task dashboard) using Testing Library.
   - Configure MSW for API mocking to support component/developer testing.

## Risks & Considerations
- Auth flows span multiple storage providers (Basic, SSO, mock); ensure new client keeps parity.
- Sidebar navigation depends on contextual permissions; validate updates against backend claims.
- Temporal task visibility relies on polling endpoints—coordinate with backend for push/subscription roadmap.

## Definition of Done (Phase 1)
- All navigation and layout components live under `src/app/` with route guards and suspense states.
- Core CRUD pages use shared data hooks with standardized loading/error UI.
- CI-friendly lint/type-check/test commands pass locally with documented setup steps.
