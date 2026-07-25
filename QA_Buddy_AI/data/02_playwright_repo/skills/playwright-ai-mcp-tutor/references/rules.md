# Repository Rules Snapshot

## Folder Mapping

- `src/pages`: page objects only (`*Page.ts`)
- `src/modules`: workflow logic (`*Module.ts`, `*Modal.ts`)
- `src/utils`: utility helpers and reusable infra
- `src/tests`: spec files (`*.spec.ts`)

## Architectural Constraints

- Tests should call modules/fixtures, not page locators directly.
- Modules should use page methods, not `page.locator()`.
- Page objects should expose locator arrow functions and simple actions.

## Validation Gate

Use the rule engine before tests:

```bash
npm run rules:check
```
