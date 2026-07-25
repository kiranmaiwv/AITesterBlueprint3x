---
name: playwright-ai-mcp-tutor
description: Teach and implement Playwright AI agent workflows (Planner, Generator, Healer) with MCP and repository guardrails. Use when preparing workshops, generating Playwright tests with architecture constraints, or enforcing deterministic code generation through a rule engine.
---

# Playwright AI MCP Tutor Skill

Use this skill to teach or execute AI-assisted test automation in this repository.

## Core Workflow

1. Read architecture constraints from `references/rules.md`.
2. Ask Planner to output scenarios, tags, and impacted files only.
3. Ask Generator to write code only in approved folders.
4. Run `npm run rules:check` and relevant tests.
5. If failing, ask Healer to patch minimal code using logs/traces.
6. Re-run rule engine and tests.

## Required Constraints

- Keep `Pages -> Modules -> Tests` layering.
- Place page objects in `src/pages`.
- Place module/modal workflow code in `src/modules`.
- Place utility code in `src/utils`.
- Keep direct locators out of modules.

## Use Prompt Templates

Load `references/prompts.md` and reuse prompts with repository-specific inputs.

## Teaching Sequence

1. Explain the three-agent model.
2. Demonstrate MCP browser grounding.
3. Run a live generate -> validate -> heal loop.
4. Make students pass `rules:check` before grading.
