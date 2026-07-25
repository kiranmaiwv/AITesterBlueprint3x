# Generator Instructions

You are the implementation agent for this Playwright framework.

## Goal

Generate code from an approved Planner output while preserving architecture and naming conventions.

## Mandatory Constraints

- Create page classes only in `src/pages` with `*Page.ts` naming.
- Create module/modal workflow classes only in `src/modules` with `*Module.ts` or `*Modal.ts` naming.
- Create utility code only in `src/utils`.
- Create tests only in `src/tests` using `*.spec.ts`.
- Use fixtures where possible.

## Coding Rules

- In pages: locators as arrow functions (`= () => this.page.locator(...)`).
- In modules: never call `.locator()` directly.
- In tests: use `test.describe()` and prefer tagged describe names.
- Avoid `console.log`; use Logger.

## Completion Criteria

1. Code compiles.
2. `npm run rules:check` passes.
3. Relevant tests are runnable.
