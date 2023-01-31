.PHONY: lint
lint:
	mypy --install-types --non-interactive .
	flake8 .

.PHONY: style
style:
	black . --check --diff
	isort . -c --diff

.PHONY: format
format:
	black .
	isort .
