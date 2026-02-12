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

(cleanup|bug|feature|refactor): quick overview 3-10 words

- Important thing 1
- Important thing 2
- NOTE: Surprising thing
- WARNING: Dangerous Thingq
- DEBT: Explain techincal debt introduced

Example #1:

bug: Fix handler wiring and day rollover after midnight / wake

- Move protocol imports from TYPE_CHECKING to top level so BaseHandler
  can resolve annotations for dependency wiring
- Add SmartNotificationHandler usecase_config_ro_repo annotation to
  fix prod AttributeError
- Add ComputeTaskRiskHandler audit_log_ro_repo wiring (was under
  TYPE_CHECKING)
- Add day rollover handling in StreamingDataProvider: reconnect/resync
  when local date changes (midnight, app wake, tab focus)
- Add wiring tests for SmartNotificationHandler and
  ComputeTaskRiskHandler
- NOTE: streamingData.tsx has new solid/reactivity lint warning on
  maybeHandleDayRollover; checks still pass

Example #2:

feature: Add first-party Lykke calendar events

- Allow calendars without auth tokens to support a built-in Lykke calendar
- Add API commands + routes for creating/deleting timed Lykke calendar entries
- Add frontend "Add event" modal and wire to calendar entry API
- Add unit tests for ensuring Lykke calendar and create/delete entry commands
- NOTE: Poetry lock regenerated (Poetry 2.3.2)
