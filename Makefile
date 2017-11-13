.PHONY: all test upgrade release

all:
	@echo 'test     run the unit tests with the current default python'
	@echo 'upgrade  run pip to check for dependency updates'
	@echo 'release  publish the current version to pypi'

test:
	@nosetests

upgrade:
	@pur -s click -r dev-requirements.txt

release:
	@python ./setup.py sdist upload
