## Change

Describe the resulting behavior and link the relevant PRD requirements or ADR.

## Validation

List automated checks and the runnable/manual verification performed. Include an application screenshot when UI behavior changes. Identify fixtures versus genuine source evidence.

## Data and operation

Describe any configuration, dependency, source-access, schema/migration, or recovery changes. Link updated operating instructions where needed.

- [ ] Applicable acceptance criteria and earlier affected behavior checked
- [ ] Change uses a dedicated branch and targets `main`
- [ ] `make check` passes
- [ ] Required GitHub CI passes on the latest PR revision before merge
- [ ] Diff reviewed and review conversations resolved
- [ ] No credentials, personal session inputs, or generated runtime data included
- [ ] Documentation and data attribution updated where affected
