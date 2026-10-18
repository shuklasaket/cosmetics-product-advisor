# Testing and test-driven development

Use test-driven development (TDD) for new or changed application behavior, repository automation, and bug fixes. Work through one acceptance criterion at a time using the existing [branch and PR workflow](git-workflow.md). Reference actual tracked stories when they exist; this guide does not create a backlog or assign story IDs.

Documentation-only changes, generated dependency exports, and changes without executable behavior can record `TDD: N/A — <reason>` in the PR's validation evidence. Run the checks relevant to those changes. Do not introduce artificial failing tests or tests that only repeat document text to claim TDD compliance.

The current foundation supplies pytest, Streamlit AppTest, isolated configuration, and offline CI. Existing passing tests establish regression coverage; they do not establish that earlier development followed TDD.

## The development cycle

1. **Select a behavior.** Start from the PRD or tracked story's acceptance criteria. Identify the observable result, inputs, and relevant invalid, empty, failure, or boundary cases. Choose the lowest test layer that can verify the behavior.
2. **Red.** Write one focused test before implementing the behavior. Run it and confirm it fails for the intended missing behavior. Fix collection, dependency, or environment problems before treating a failure as feature evidence. For a bug, reproduce it with a failing regression test first.
3. **Green.** Implement enough production code to satisfy the test. Assert the required behavior rather than bypassing validation, weakening the test, or hard-coding a fixture-specific answer.
4. **Refactor.** Improve names, boundaries, and duplication while keeping tests passing. Verify the affected tests after any refactoring; record when no refactoring was needed.
5. **Repeat and verify.** Add the next behavior or edge case. Before publishing, run `make check`, inspect the diff, and record the evidence in the PR. Required GitHub CI must pass on the latest revision before merge.

Keep the feedback loop focused while working. For example, this command runs an existing foundation test file; substitute the actual feature test file or pytest node ID as code is introduced:

```sh
uv run --frozen pytest tests/test_settings.py -x
make check
git diff --check
```

Do not push deliberately failing commits solely to demonstrate Red, or require a separate commit for each phase. A passing final suite and honest PR evidence support review; CI cannot prove the order in which code and tests were written.

## What to test and where

Keep most tests fast and focused, add integration tests for real local boundaries, and use a small number of full workflow checks. Add test modules alongside the functionality they verify; create subdirectories only when they improve navigation.

| Area | Test approach and priority cases |
| --- | --- |
| Validation and deterministic policies | Unit tests for accepted/rejected inputs, integer-paise budget boundaries, ingredient applicability, score vectors, and stable tie-breaking as their PRDs arrive. |
| SQLite imports and persistence | Temporary real databases for schema creation/migrations, duplicate handling, provenance retention, transactional rollback, and preservation of the last valid catalog. |
| Source and model adapters | Recorded or synthetic boundary responses for success, timeout, malformed data, invalid structured output, and missing evidence. Exercise actual local parsing and policy code. |
| Streamlit UI | AppTest for form submission, session transitions, visible results, and empty/error/recovery states. Use manual Mac checks for behavior AppTest cannot establish. |
| Privacy and memory | Tests that inspect stores, logs, and exports where applicable; verify session-only inputs are not persisted and saving preferences requires the specified user action. |
| Release evidence | Explicit checks using permitted genuine catalog/review evidence, target-Mac model benchmarks, and frozen evaluation cases required by the relevant PRD. |

Each implemented acceptance criterion needs observable verification. Cover hard eligibility rules, data integrity, failure paths, and privacy boundaries before cosmetic assertions or implementation details. Do not test framework internals, trivial accessors, or exact incidental call sequences. Bug regression tests must fail against the faulty behavior and pass with the fix.

Coverage percentages are diagnostic, not a substitute for these cases. There is currently no coverage plugin or numeric coverage gate; neither is required to start TDD. Add one deliberately when it helps identify meaningful gaps.

## Fixtures and external boundaries

- Routine tests run with outbound network sockets blocked. Local Unix sockets remain allowed for Streamlit's event loop. The shared [fixture setup](../tests/conftest.py) clears `ADVISOR_` environment variables and changes each test's working directory to a temporary directory, avoiding the developer's real `.env` file.
- Use `tmp_path` for SQLite files and fixed or injected clocks for freshness and timeout logic. Isolate tests from the developer's databases, saved preferences, and installed models.
- Fake external source/model boundaries rather than local business logic. Keep adapter-contract tests separate from any explicit checks that establish compatibility with a genuine source or model.
- Label synthetic fixtures and keep them separate from genuine product evidence under the [data policy](../data/README.md). Recorded evidence needs provenance, permission for reuse, and removal of personal data or secrets.
- Keep live source/model checks under the existing `live` marker, which routine pytest excludes. Live execution needs explicitly configured fixtures, permitted access, and network settings; do not silently enable it in routine TDD or CI.
- For model-assisted features, assert valid schemas, supported claims/citations, bounded retries/usage, and unchanged deterministic decisions. Do not assert byte-identical generated prose. Offline controlled responses do not establish real-model quality; record genuine evaluations separately.

## PRD 01 example

These are test cases derived from [CAT-02, CAT-05, and CAT-07](requirements/01-catalog-and-search.md), not new user stories or an implemented API:

| Case | Expected behavior |
| --- | --- |
| Matching category and India availability; price and budget both 80,000 paise | Product is included at the inclusive ceiling. |
| Same product facts; price 80,001 paise and budget 80,000 paise | Product is excluded. |
| Unknown price or unknown availability | Product is excluded from budget-qualified results. |
| Budget is zero | Input is accepted; results still depend on the eligible catalog facts. |
| Import fails after writes begin | Transaction is rolled back and the previous valid catalog remains searchable. |

Implement one case at a time through Red, Green, and Refactor. Use synthetic catalog fixtures for the fast loop and a temporary SQLite database for the import case. PRD 01 still requires its separately verified genuine seed dataset and local deployment checks; synthetic fixtures do not satisfy that release evidence.

## PR evidence and completion

In the [PR template](../.github/PULL_REQUEST_TEMPLATE.md), use **Checks** to record the focused test command or node ID, the observed initial failure, the passing result after implementation, and verification after refactoring (or why none was needed). Include the final `make check` result. Summarize related cases together when useful; a full terminal transcript is unnecessary. For exempt changes, give a specific `TDD: N/A — <reason>` and the checks actually run.

Use **Acceptance criteria** to map the changed criteria to tests or explicitly recorded release checks. Distinguish synthetic fixtures, recorded responses, and genuine evaluations. Disclose unrun checks and remaining gaps; never reconstruct Red evidence that was not observed. If implementation preceded the test, state that limitation and provide the regression evidence actually available.

Reviewers assess behavior coverage and the credibility of that evidence. The metadata validator checks the existing PR structure and required fields; it does not validate TDD chronology or the truth of results. Follow the [Definition of Done](development.md#definition-of-done) and wait for the required GitHub check before merging.

References: [TDD cycle](https://martinfowler.com/bliki/TestDrivenDevelopment.html), [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing).
