
.PHONY: all
all: docs distr

.PHONY: docs
docs: mimedecode.html mimedecode.man mimedecode.txt

include Makefile.xsltproc

.PHONY: distr
distr:
	./mk-distr


CLEANFILES = *.py[co] MANIFEST

.PHONY: clean
clean:
	rm -f $(CLEANFILES)
