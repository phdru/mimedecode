
VERSION=$(shell python -c "from __version__ import __version__; print __version__")

.PHONY: all
all: docs sdist

DISTFILES = \
ANNOUNCE \
INSTALL.txt \
MANIFEST.in \
Makefile \
Makefile.4xslt \
Makefile.sgmlt \
Makefile.xsltproc \
mimedecode.docbook \
mimedecode.html \
mimedecode.man \
mimedecode.py \
mimedecode.txt \
mimedecode_version.py \
setup.py

.PHONY: sdist
sdist: dist/mimedecode-$(VERSION).tar.gz

.PHONY: dist
dist/mimedecode-$(VERSION).tar.gz: $(DISTFILES)
	umask 022 && chmod a+rX $(DISTFILES) && python setup.py sdist --formats=bztar

.PHONY: docs
docs: mimedecode.man mimedecode.txt mimedecode.html

include Makefile.xsltproc


CLEANFILES = *.py[co] MANIFEST

.PHONY: clean
clean:
	rm -f $(CLEANFILES)

.PHONY: distclean
distclean: clean
	rm -rf dist
