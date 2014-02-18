
.PHONY: all
all: docs test clean distr


.PHONY: docs
docs: mimedecode.html mimedecode.man mimedecode.txt

include Makefile.xsltproc


.PHONY: distr
distr:
	./mk-distr


.PHONY: test
test:
	make -C test all


CLEANFILES = *.py[co] MANIFEST

.PHONY: clean
clean:
	rm -f $(CLEANFILES)
	make -C test clean
