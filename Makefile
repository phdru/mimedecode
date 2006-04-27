
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

sdist: dist/mimedecode-2.1.0.tar.gz
	touch sdist

dist/mimedecode-2.1.0.tar.gz: $(DISTFILES)
	umask 022 && python setup.py sdist

docs: mimedecode.man mimedecode.txt mimedecode.html

include Makefile.4xslt


CLEANFILES = mimedecode.pyc MANIFEST sdist

clean:
	rm -f $(CLEANFILES)

distclean: clean
	rm -rf dist sdist
