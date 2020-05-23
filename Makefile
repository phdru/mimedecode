
.PHONY: all
all: docs test clean distr


.PHONY: docs
docs:
	make -C docs html man text


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
