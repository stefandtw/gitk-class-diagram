
GV:=fdp
GITK:=gitk
CTAGS:=ctags
PY:=python3

help:
	@echo "make check-depends"
	@echo "	Check whether all required dependencies are present"
	@echo "make install"
	@echo "	Install the application"
	@echo "make install-editable"
	@echo "	Install the application using links to this source"
	@echo " directory."
	@echo "make uninstall"
	@echo "	Delete installed files"
	@echo "make test-python"
	@echo "	Execute tests, which create tests/*.actual.gv files"
	@echo "make test-images"
	@echo "	Generate PNGs for all tests/*.gv files."
	@echo "	Useful if tests fail, to check differences visually."
	@echo "make test-update-expected"
	@echo "	Use tests/*.actual.gv as future tests/*.expected.gv."
	@echo "	Compare actual and expected PNGs before you use this."
	@echo "make lint"
	@echo "	Run lint tool"

check-depends:
	@echo "Checking dependencies"
	@which $(GITK)
	@git version
	@$(GV) -V
	@$(CTAGS) --version
	@$(PY) --version

test: test-python

test-python: clean-test-python
	$(PY) -m tests.test_classdiff

clean-test-python:
	rm -f tests/*.actual.gv

tests/%.png: tests/%.gv
	$(GV) -Tpng -o $@ $<

test-images: clean-test-images $(patsubst %.gv,%.png,$(wildcard tests/*.gv))

clean-test-images:
	rm -f tests/*.png

test-update-expected: tests/*.actual.gv
	$(foreach file,$^,cp $(file) $(patsubst %.actual.gv,%.expected.gv,$(file));)

install:
	pip install .

install-editable:
	pip install -e .
	rm -f /usr/bin/gitk-cl
	ln -s $$(readlink -f gitk-cl) /usr/bin/gitk-cl

install-from-pypi:
	pip install gitk-class-diagram

uninstall:
	pip uninstall gitk-class-diagram

lint:
	flake8

package:
	python3 setup.py sdist bdist_wheel

clean-setup:
	python3 setup.py clean

.PHONY: check-depends test-python clean-test-python test-images clean-test-images install uninstall lint package clean-setup
