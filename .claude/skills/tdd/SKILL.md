---
name: tdd
description: Use this skill when implementing any function with business logic, especially in `server/services/`. Captures the red-green pattern: define validation before writing implementation. Activate when adding a feature, fixing a bug with behavioral change, or any time the task says "implement" or "add".
---

# Purpose

You write tests before code. Before any implementation, you define what "correct" looks like as an executable check. Tests describe intent; implementation has to match intent, not the other way around. This is the operator's preferred development pattern — captured here so you follow it instead of the LLM default of "implement first, test after".

## Variables

- `$TEST_DIR` — `server/tests/`. New tests land here.
- `$TEST_RUNNER` — `cd server && uv run pytest`. Use to verify red/green at each step.
- `$SERVICE_DIR` — `server/services/`. Most skill activations target functions here.

## Instructions

- One test at a time. Not "write all tests then all code".
- Edge cases over coverage. 3–5 cases that would break a naive implementation, not exhaustive enumeration.
- Refactor only when all tests are green. Tests stay green through refactor.
- The edge case list IS the thinking. Write it down before writing code.
- Activate for: new functions in services, behavior-changing edits, bug fixes (the bug is your first red test), new endpoints.
- Skip for: pure refactors (no behavioral change), frontend-only changes (use `pinchtab` skill instead), typos / renames / imports.

## Workflow

1. List 3–5 edge cases that would break a naive implementation. Write them as comments at the top of the test file. Examples: `None` field, empty list, duplicate key, off-by-one, concurrent insert.
2. Pick one edge case. Write a pytest function in `$TEST_DIR` that exercises the desired behavior.
3. Run `$TEST_RUNNER`. The new test **must fail** (assertion error or import error). If it passes against current code, the test isn't testing what you think — fix the test.
4. Write the smallest implementation in `$SERVICE_DIR` that makes the test pass. No features the test doesn't require.
5. Run `$TEST_RUNNER`. The new test passes. All prior tests still pass.
6. Pick the next edge case. Repeat steps 2–5.
7. When edge case list is exhausted: refactor pass for clarity. Tests stay green throughout.

## Output Format

- New test file: `$TEST_DIR/test_<feature>.py` containing the edge case comments + pytest functions
- New or modified implementation: `$SERVICE_DIR/<feature>.py` with type hints (per CLAUDE.md)
- Route wiring if needed (per CLAUDE.md: routes thin, services do the work)

## Report

When done, summarize back to the caller:
- Edge cases covered (list)
- Test file path + test count
- Implementation file path
- `$TEST_RUNNER` output line: `N passed`
- Any edge case you considered and skipped, with reason
