# Write a GitHub PR summary for the current branch

## Goal

Produce a **solid, copy-paste-ready markdown** pull request summary for the branch currently checked out. The output should be suitable for the PR description field on GitHub.

## Steps

1. **Get branch and diff context**
   - Run `git branch --show-current` to get the current branch name.
   - Determine the base branch: use `main` if it exists, otherwise `master`.
   - Run `git log <base>..HEAD --oneline` to list commits on this branch.
   - Run `git diff <base>...HEAD --stat` to see which files changed and how much.
   - Optionally run `git diff <base>...HEAD` (or a subset of paths) if you need more detail to describe behavior changes.

2. **Analyze the changes**
   - From commits and diffs, infer: what was added, fixed, refactored, or removed.
   - Note any new dependencies, config, or migrations.
   - Note testing (new/updated tests, or gaps) and any manual verification that makes sense.

3. **Write the PR summary in markdown**
   - Use the format below so the result is easy to copy and paste into GitHub.
   - Output the entire summary inside a **single markdown code block** (triple backticks with `markdown` label) so the user can copy it in one go and paste into the PR description.

## Required PR summary format

Use this structure. Adapt section titles and bullets to the actual changes; remove sections that don’t apply.

```markdown
## Summary
<!-- One short paragraph: what this PR does and why -->

## Changes
- 
- 

## Testing
- 

## Notes / follow-ups
<!-- Optional: migrations, config, tech debt, or follow-up work -->
```

## Output instructions

- **Emit the full PR summary inside one fenced code block** so it can be copied and pasted directly, e.g.:

  ````text
  ```markdown
  ## Summary
  ...

  ## Changes
  ...

  ## Testing
  ...

  ## Notes / follow-ups
  ...
  ```
  ````

- Use clear, concise bullets. Prefer past tense for completed work (e.g. "Add user check-ins table and migration").
- If the branch has multiple logical changes, group them under **Changes** (e.g. backend vs frontend, or feature vs cleanup).
- Keep **Summary** to 2–4 sentences; **Testing** should mention how to verify or what was tested.
- Do **not** include the branch name or base branch in the markdown body unless it’s relevant (e.g. for release branches); the PR title can be derived from the summary by the user.
