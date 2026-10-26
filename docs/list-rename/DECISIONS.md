## BRANCH DECISIONS: feature/list-rename

2026-10-07: Rename a list in place.
Context: A list could only be named when it was created.
Decision: Clicking the list title makes it editable. Enter or leaving the field saves, Escape cancels. The list update endpoint (PATCH) now accepts an optional "name". Empty names are rejected and surrounding spaces are trimmed.
Alternatives considered: A separate rename button or dialog, rejected as heavier than needed for a small action.
Consequences: Users can fix a list name without recreating the list.
