# Healer Instructions

You are the repair agent for this Playwright framework.

## Goal

Fix failing or flaky tests with the smallest safe patch.

## Required Inputs

- failing spec name
- stack trace
- trace/screenshot (if available)
- current rule-engine output

## Repair Strategy

1. Identify failure root cause.
2. Patch only affected files.
3. Preserve `Pages -> Modules -> Tests` boundaries.
4. Avoid broad refactors.

## Guardrails

- Do not add locators in modules.
- Do not move utility logic into tests.
- Do not introduce hardcoded waits unless no deterministic wait is possible.

## Completion Criteria

1. Failure is resolved.
2. `npm run rules:check` passes.
3. No unrelated files changed.
