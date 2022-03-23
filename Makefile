PYTHON ?= python3

.PHONY: dist doc dep_install
dep_install:
	$(PYTHON) -m pip install setuptools wheel twine

dist:
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY: upload
upload:
	$(PYTHON) -m twine upload dist/*
clean:
	rm -rf build dist pyuwb.egg-info *.bak
doc:
	pydoc-markdown -I pyuwb -m pyuwb --render-toc > doc/pyuwb_api.md

.PHONY: test
test:
	pytest

