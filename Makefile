# Makefile

install:
	pip3 install -r requirements.txt

test:
	python3 -m pytest -vv --tb=no --disable-warnings ./tests/

test-cov:
	python3 -m pytest --cov . --cov-fail-under=80

test-cov-miss:
	python3 -m pytest --cov . --cov-report term-missing

lint:
	python3 -m pylint --disable=R,C --fail-under=8 prep.py main.py

all:
	install test test-cov lint
