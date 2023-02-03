# Makefile

install:
	pip3 install -r requirements.txt

lint:
	python3 -m pylint --disable=R,C --fail-under=8 prep.py main.py

test:
	python3 -m pytest -vv --tb=no --disable-warnings ./tests/

test-cov:
	python3 -m pytest --cov .

test-cov-miss:
	python3 -m pytest --cov . --cov-report term-missing

all:
	install lint test test-cov
