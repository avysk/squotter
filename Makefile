test: check
	@python setup.py nosetests --with-coverage --cover-erase --cover-package=squirrel_tree --cover-html

check:
	@pep8 squirrel_tree/
	@pep8 tests/
	@pylint -r n squirrel_tree/
	@pylint -r n tests/
	@python setup.py flake8

dist: clean test
	@python setup.py sdist

clean:
	rm -rf cover .coverage dist *.egg-info build
	find . -name '*.pyc' -delete

.PHOny: check test dist clean
