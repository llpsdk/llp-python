.PHONY: test
test:
	uv run pytest
	uv run mypy src/llpsdk
	uv run ruff check src/llpsdk

.PHONY: format
format:
	uv run black src/llpsdk
