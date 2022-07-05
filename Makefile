# Makefile

install:
	pip3 install -r requirements.txt

test:
	python3 -m pytest -vv --tb=no --disable-warnings ./tests/

lint:
	python3 -m pylint --disable=R,C --fail-under=8 prep.py main.py

all:
	install test lint
