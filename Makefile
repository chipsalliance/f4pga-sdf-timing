# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

# Use bash even on Windows
SHELL := /bin/bash

# On Windows the activate script is stored in a different location.
ACTIVATE_SCRIPT := venv/bin/activate
ifeq ($(OS),Windows_NT)
ACTIVATE_SCRIPT := venv/Scripts/activate
endif

ACTIVATE=[[ -e $(ACTIVATE_SCRIPT) ]] && source $(ACTIVATE_SCRIPT);

clean:
	rm -rf build dist *.egg-info

.PHONY: clean

venv-clean:
	rm -rf venv

.PHONY: venv-clean

$(ACTIVATE_SCRIPT): requirements.txt setup.py Makefile
	make venv
	@ls -l $(ACTIVATE_SCRIPT)
	@touch $(ACTIVATE_SCRIPT)
	@ls -l $(ACTIVATE_SCRIPT)

venv:
	virtualenv --python=python3 --always-copy venv
	# Packaging tooling.
	${ACTIVATE} pip install -U pip twine build
	# Setup requirements.
	${ACTIVATE} pip install -r requirements.txt
	@${ACTIVATE} python -c "from sdf_timing.version import version as v; print('Installed version:', v)"
	# Infra requirements.
	${ACTIVATE} pip install git+https://github.com/mithro/actions-includes.git

.PHONY: venv

# Packaging and uploading to PyPI
build: | $(ACTIVATE_SCRIPT)
	${ACTIVATE} python -m build --sdist
	${ACTIVATE} python -m build --wheel

.PHONY: build

PYPI_TEST = --repository-url https://test.pypi.org/legacy/
upload-test: | $(ACTIVATE_SCRIPT)
	make clean
	make build
	${ACTIVATE} twine upload ${PYPI_TEST} dist/*

.PHONY: upload-test

upload: | $(ACTIVATE_SCRIPT)
	make clean
	make build
	${ACTIVATE} twine upload --verbose dist/*

.PHONY: upload

check: | $(ACTIVATE_SCRIPT)
	make clean
	make build
	${ACTIVATE} twine check dist/*.whl

.PHONY: check

install: | $(ACTIVATE_SCRIPT)
	${ACTIVATE} python setup.py install

.PHONY: install

# Testing the library
TEST_LIKE_CI_RUN_SH := venv/actions/includes/actions/python/run-installed-tests/run.sh
$(TEST_LIKE_CI_RUN_SH):
	if [ ! -d venv/actions ]; then git clone https://github.com/SymbiFlow/actions venv/actions; fi
	cd venv/actions && git pull

test-like-ci: | $(TEST_LIKE_CI_RUN_SH) $(ACTIVATE_SCRIPT)
	${ACTIVATE} $(TEST_LIKE_CI_RUN_SH)

.PHONY: test-like-ci

test: | $(ACTIVATE_SCRIPT)
	${ACTIVATE} pytest

.PHONY: test

version: | $(ACTIVATE_SCRIPT)
	${ACTIVATE} python setup.py --version

.PHONY: version

# Format the code
GHA_WORKFLOW_SRCS = $(wildcard .github/workflows-src/*.yml)
GHA_WORKFLOW_OUTS = $(addprefix .github/workflows/,$(notdir $(GHA_WORKFLOW_SRCS)))

.github/workflows/%.yml: .github/workflows-src/%.yml | $(ACTIVATE_SCRIPT)
	${ACTIVATE} python -m actions_includes $< $@

format-gha: $(GHA_WORKFLOW_OUTS) | $(ACTIVATE_SCRIPT)
	@echo $(GHA_WORKFLOW_OUTS)
	@true

.PHONY: format-gha

format:
	$(MAKE) format-gha

.PHONY: format
