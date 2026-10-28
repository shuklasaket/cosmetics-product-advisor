# PRD 08 — Opt-In Preference Memory

Status: Draft · Dependencies: [PRD 07](07-conversational-workflow.md) · Source: report §§9–11, 14–15, 17

## Problem and outcome

Returning shoppers repeat stable preferences, while personal exclusions and medical information should not become a permanent profile. The application needs a small, understandable memory with explicit save and clear controls.

**Minimum deployable increment:** a local preferences panel that saves and reuses three allowed preferences across app restarts, while conversation and sensitive inputs remain session-only.

**Smallest delivery path:** add one validated local-profile record in the existing
SQLite database and a direct, reviewed save action in Streamlit. Reuse these values as
visible defaults in the form and conversation. Preference operations stay outside the
five-role workflow: no role can infer consent, read hidden preference data, or write it.
No general memory agent, embedding store, conversation archive, or identity service is required.

## Goals and scope

- Demonstrate cross-session reuse of currency, purchase country, and preferred product finish.
- Save nothing before opt-in and persist nothing outside an explicit field allowlist.
- Let the user inspect, edit, clear, or disable saved preferences with immediate effect.

The release serves one local profile on one installation. Accounts, multi-user identity, cross-device sync, vector memory, remembered allergies, raw chat archives, and automatic extraction of permanent preferences from conversation are deferred.

## Must-have requirements

| ID | Requirement and acceptance condition |
| --- | --- |
| MEM-01 | Show an initially disabled “Remember preferences on this device” control and explain the three fields stored in local SQLite. Enabling it alone does not save unreviewed conversation text; saving requires an explicit reviewed preference action. |
| MEM-02 | Allowlist only `preferred_currency`, `preferred_purchase_country`, and `preferred_product_finish`. Currency/country accept only currently supported INR/India; finish accepts a documented product preference value. Reject unknown keys and allergy/exclusion/medical fields even when supplied by a role, model, or malformed client payload. |
| MEM-03 | Provide validated `save_preferences` and `get_preferences` tools outside role capability sets. The save tool requires the controller's session-recorded user-save action, not a role/model claim that consent exists. Writes are idempotent; a failed write reports failure and leaves the previous stored values intact. |
| MEM-04 | Reuse saved values as visible defaults on a later session/restart and label their origin. An explicit current request overrides a saved value for that run; it changes long-term memory only through another reviewed save. Unsupported/corrupt stored values are ignored with an explanation. |
| MEM-05 | Keep ingredient exclusions, allergy/medical details, current budget, raw conversation, and non-minimum role payloads in session memory only. Raw graph checkpoints remain disabled. Persistent logs/caches contain no sensitive inputs or user-specific matching details; inspect database, logs, and exports to verify this boundary. |
| MEM-06 | Provide separate “Clear current session” and “Delete saved preferences” actions. Session clear removes conversation, budget, exclusions, and active result state. Deletion removes all saved values and disables opt-in; later sessions cannot restore deleted preferences from caches or logs. Turning memory off also deletes saved values. |
| MEM-07 | Display the current saved values and storage status. If SQLite is unavailable, the conversation continues without long-term memory and says that preferences were not saved. Do not present session-only recall as successful cross-session memory. |

## Release verification

Start with a fresh profile, choose India/INR/matte, review and save, then restart the app. Confirm all three values are reused and visibly attributed to memory. Override matte with another finish in one request and confirm the stored finish changes only after a separate save.

Without opting in, enter an exclusion and a sensitive medical phrase; restart and inspect all persistent stores to confirm neither was retained. Attempt an unauthorized memory-tool write, corrupt a stored value, simulate a failed write, delete saved preferences, and clear a session. Confirm the expected rejection, recovery, deletion, and separation of short-term versus long-term memory.

## Success measures

- 3/3 allowed preferences are correctly reused after restart in acceptance tests.
- Zero unapproved or sensitive fields appear in persistent stores or evaluation exports.
- 100% of delete/disable tests prevent preference recovery in a subsequent session.

## Dependencies and decisions

SQLite remains the only persistent preference store. The one-profile boundary must be visible; public/multi-user deployment would require a separately specified identity and isolation design. Engineering verifies the privacy boundary across prior logs and caches before enabling memory.
