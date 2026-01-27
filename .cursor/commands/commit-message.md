# Write a good commit message

## How This Works

run `git diff --staged` to see all of the changes I plan to commit.

Anlyze these changes, and confirm:

- Is well tested -- confirm unit tests have been added to cover any new functionality.
- Confirm that the new changes follow the existing design paradigms and don't violoate: DDD, Hexagonal architecture, DRY, Clean.

If you find any problems please tell me and suggest a solution.

If there are no issues, then do:

- `nvm use 25 && ./check-all.sh` passes -- if anything fails fix them and then continue
- write a commit message, follow this pattern:

Non Technical Explanation (max 100 characters)

- Important thing 1
- Important thing 2
- NOTE: Surprising thing
- WARNING: Dangerous Thing
- DEBT: Explain techincal debt introduced

NOTE: Don't convert the bullets to markdown, they don't copy paste well.
