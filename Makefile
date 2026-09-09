.PHONY: install test coverage seed clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

coverage:
	coverage run -m pytest && coverage report

seed:
	python -m trial_booking seed

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info src/*.egg-info .coverage
	find . -name __pycache__ -exec rm -rf {} +
