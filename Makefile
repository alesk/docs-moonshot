#; -*-mode: GNUmakefile; -*-
NPROCS := $(shell python -c "import multiprocessing; print(multiprocessing.cpu_count())")

AVRO_TOOLS = java -jar generated/avro-tools.jar idl

.DEFAULT_GOAL := docs

generated/avro-tools.jar:
	curl http://www.apache.si/avro/avro-1.8.1/java/avro-tools-1.8.1.jar -o $@

generated/%.avpr : avdl/%.avdl generated/avro-tools.jar
	@echo "Generating " $@
	@$(AVRO_TOOLS) $< > $@

.PHONY: docs
docs: generated/etl.avpr generated/platform.avpr
	@python schema_to_rst.py --protocol-path generated --output-path schema/generated
	@sphinx-build -b html -d _build/doctrees . _build/html -j $(NPROCS)

.PHONY: clean
clean:
	@rm -rf generated/*.avpr schema/generated _build/html/* _build/doctrees/*
