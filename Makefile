-include local.mk

all: requirements install flake8 typecheck unittest xcop

clean:
	rm -rf build
	rm -rf veniq.egg-info
	rm -rf dist

requirements:
	python3 -m pip install -r requirements.txt

unittest:
	python3 -m unittest discover
	python3 -m unittest test/integration/dataset_collection.py

install:
	python3 -m pip install .

xcop:
	xcop $(find . -name '*.xml')

flake8:
	python3 -m flake8 veniq test

typecheck:
	python3 -m mypy veniq test
