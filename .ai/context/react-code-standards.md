---
name: react-code-standards
globs: "**/*.{ts,tsx,js,jsx}"
alwaysApply: true
description: Standards for building scalable, maintainable React and Next.js applications with strong modularity, type safety, and predictable UI architecture
---

- Follow feature/domain-oriented architecture with clear separation of concerns
- Prefer modular and composable UI architecture over deeply coupled components
- Use **TypeScript everywhere** with strict typing enabled
- Avoid `any` unless absolutely necessary and explicitly justified
- Prefer explicit and predictable state flows
- Keep components small, focused, and single-purpose
- Separate UI, business logic, and data-fetching concerns
- Prefer composition over inheritance
- Avoid prop drilling when architectural alternatives are more appropriate
- Prefer server components where appropriate in Next.js
- Minimize unnecessary client-side state
- Prefer React Query / TanStack Query patterns for async state management
- Keep hooks deterministic and side-effect-safe
- Avoid hidden side effects in hooks and components
- Prefer derived state over duplicated state
- Avoid large monolithic components
- Keep business logic outside presentation components
- Use shared UI primitives/design system components consistently
- Prefer semantic HTML and accessibility-first development
- Ensure keyboard accessibility and reasonable ARIA usage
- Prefer responsive layouts by design
- Avoid hardcoded magic values in styling or layout logic
- Use meaningful naming for components, hooks, variables, and actions
- Prefer explicit loading, error, and empty states
- Avoid unnecessary re-renders and expensive computations in render paths
- Memoization should only be used when justified by measurable benefit
- Prefer declarative code over imperative DOM manipulation
- Avoid deeply nested conditional rendering
- Prefer clear API contracts between frontend and backend
- Validate external data at application boundaries
- Prefer centralized API clients and typed DTOs/contracts
- Avoid duplicated API logic across components
- Keep styling predictable and maintainable
- Avoid unstructured global CSS
- Prefer design tokens and reusable spacing/typography systems
- Prefer Tailwind utility consistency or structured CSS modules strategy
- Avoid overengineering frontend abstractions
- Optimize for maintainability and developer experience
- All comments and log messages must be in **English**
- Comment only non-trivial logic; avoid obvious or redundant comments