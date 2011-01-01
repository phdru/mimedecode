
VERSION=$(shell python -c "from mimedecode import _version; print _version")

all: docs sdist

DISTFILES = mimedecode.py \
setup.py \
Makefile \
Makefile.sgmlt \
Makefile.4xslt \
MANIFEST.in \
ANNOUNCE \
mimedecode.docbook \
mimedecode.html \
mimedecode.man \
mimedecode.txt

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
