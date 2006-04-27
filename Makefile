
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
sdist: dist/mimedecode-2.1.0.tar.gz

.PHONY: dist
dist/mimedecode-2.1.0.tar.gz: $(DISTFILES)
	umask 022 && chmod a+rX $(DISTFILES) && python setup.py sdist

.PHONY: docs
docs: mimedecode.man mimedecode.txt mimedecode.html

include Makefile.4xslt


CLEANFILES = mimedecode.pyc MANIFEST sdist

.PHONY: clean
clean:
	rm -f $(CLEANFILES)

.PHONY: distclean
distclean: clean
	rm -rf dist sdist
