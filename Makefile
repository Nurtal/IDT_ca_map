.PHONY: test test-py test-js build

test: test-py test-js

test-py:
	PYTHONPATH=pipeline python3 -m unittest discover -s tests/py

test-js:
	node --test 'tests/js/*.test.js'

build:
	python3 pipeline/cli.py build
