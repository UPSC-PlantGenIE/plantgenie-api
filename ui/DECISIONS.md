# Decisions

UI decision records. Newest last. Entries are not edited after the fact; a
changed decision gets a new entry that supersedes the old one.

## 2026-11-02: Single form for creating a list

Context: creating a list was a three-step wizard for three small choices. Giving
each step its own URL needed guards and history handling, and pressing Back
after a refresh still flashed an old step's URL.

Decision: `/lists/new` is one page with taxon, genome, name and description, and
one Create list button. The choices live in the page's own state, not Redux.

Alternatives: wizard with a URL per step (the problems above; rejected). Wizard
without URLs per step (browser Back leaves the wizard; rejected).

Consequences: no guards, nested routes or `wizardSlice`. Refreshing or leaving
clears the form, including a typed name. The page is longer on a phone. More
steps during creation would be a reason to reconsider.
