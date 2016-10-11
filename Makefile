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
	@python teftel-docs/bin/schema-to-rst.py --protocol-path generated --output-path demo/schema/generated
	@sphinx-build -b html -d _build/doctrees demo _build/html -j $(NPROCS)

.PHONY: teftel-docs
teftel-docs:
	@python teftel-docs/bin/schema-to-rst.py --protocol-path ../../toptal/teftel/generated --output-path ../../toptal/teftel/docs/user/generated/schema
	@sphinx-build -b html -d _build/doctrees ../../toptal/teftel/docs/user/ _build/html -j $(NPROCS)

.PHONY: lint
lint: ## lints Python code in accordance to PEP-8
	@flake8 .

.PHONY: clean
clean:
	@rm -rf generated/*.avpr demo/schema/generated _build/html/* _build/doctrees/*
