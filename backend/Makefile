
.PHONY: serve
serve:
	poetry run uvicorn planned.app:app --host 0.0.0.0 --port 8080 --reload


.PHONY: test
test:
	ENV_FILE=.env.test poetry run pytest tests --vcr-record=once