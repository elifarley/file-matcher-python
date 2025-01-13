.PHONY: all dist d clean c version v install i install-test itest install-dev idev install-dist idist test t build b

all: clean test version

dist d: build
	scripts/check-version.sh
	# Win MSYS2 support: force config file location
	twine upload $$(test -e ~/.pypirc && echo '--config-file ~/.pypirc') dist/*

clean c:
	rm -rfv out dist build/bdist.* src/*.egg-info

version v:
	git describe --tags ||:
	python -m setuptools_scm

install i:
	pip install --upgrade -e . \
	&& pip show orgecc-file-matcher

install-test itest:
	pip install --upgrade -e .[test] \
	&& pip show orgecc-file-matcher

install-dev idev:
	pip install --upgrade -e .[dev] \
	&& pip show orgecc-file-matcher

install-dist idist:
	pip install --upgrade -e .[dist] \
	&& pip show orgecc-file-matcher

test t:
	pytest --tb=short tests/filematcher_corpus_test.py

build b:
	# SETUPTOOLS_SCM_PRETEND_VERSION=0.0.1
	python -m build
