.PHONY: serve test typecheck check test-target

serve:
	poetry run uvicorn planned.app:app --host 0.0.0.0 --port 8080 --reload

test:
	ENV_FILE=.env.test poetry run pytest tests --vcr-record=once

typecheck:
	poetry run mypy planned

check:
	make typecheck
	make test


.PHONY: test-target
test-target:
	ENV_FILE=.env.test poetry run pytest tests --vcr-record=once -k '$(TARGET)' -s -v