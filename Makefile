.PHONY: all test upgrade clean build upload

all:
	@echo 'test     run the unit tests with the current default python'
	@echo 'upgrade  run pip to check for dependency updates'
	@echo 'release  publish the current version to pypi'

test:
	@pytest --cov=./pur

upgrade:
	@pur --skip click -r dev-requirements.txt

release: clean build upload

clean:
	@rm -f dist/*

build:
	@python ./setup.py sdist

upload:
	@twine upload ./dist/*
