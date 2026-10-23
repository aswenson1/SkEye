#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
[ ! -f requirements-dev.txt ] || .venv/bin/pip install -r requirements-dev.txt

source .venv/bin/activate