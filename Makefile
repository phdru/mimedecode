
.PHONY: all
all: distr docs

.PHONY: distr
distr:
	./mk-distr

.PHONY: docs
docs: mimedecode.man mimedecode.txt mimedecode.html

include Makefile.xsltproc


CLEANFILES = *.py[co] MANIFEST

.PHONY: clean
clean:
	rm -f $(CLEANFILES)
