# Write a good commit message

## How This Works

run `git diff --staged` to see all of the changes I plan to commit (ignore netlify.toml).

Anlyze these changes, and confirm:

- Is well tested -- confirm unit tests have been added to cover any new functionality.
- All python imports are at the top of the file (check every \*.py file)
- There are no repetetive comments. Docstrings and informative comments are good! Comments that say what the code below does are a waste.
- Confirm that the new changes follow the existing design paradigms and don't violoate: DDD, Hexagonal architecture, DRY, Clean.

If you find any problems please tell me and suggest a solution.

If there are no issues, then do:

- `nvm use 25 && ./check-all.sh` passes -- if anything fails fix them and then continue
  - to run frontend only: `cd frontend && nvm use 25 && node run check`
  - to run backend:
    - tests: make test
    - mypy: make typecheck
    - all: make check

- write a commit message, follow this pattern:

Non Technical Explanation (max 100 characters)

- Important thing 1
- Important thing 2
- NOTE: Surprising thing
- WARNING: Dangerous Thing
- DEBT: Explain techincal debt introduced

NOTE: Don't convert the bullets to markdown, they don't copy paste well.
