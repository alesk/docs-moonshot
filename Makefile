#; -*-mode: GNUmakefile; -*-
NPROCS := $(shell python -c "import multiprocessing; print(multiprocessing.cpu_count())")


.PHONY: docs
docs: 
	@sphinx-build -b html -d _build/doctrees . _build/html -j $(NPROCS)

