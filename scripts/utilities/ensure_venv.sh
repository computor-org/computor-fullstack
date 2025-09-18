#!/bin/bash
# Utility functions for activating the local virtual environment.

set -euo pipefail

ensure_venv() {
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    return
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local project_root
  project_root="${script_dir%/scripts/utilities}"

  for candidate in ".venv" "venv"; do
    if [[ -d "${project_root}/${candidate}" ]]; then
      # shellcheck disable=SC1090
      source "${project_root}/${candidate}/bin/activate"
      return
    fi
  done

  echo "❌ No virtual environment found (.venv or venv)." >&2
  echo "Please create one with 'python3 -m venv .venv' and install dependencies." >&2
  exit 1
}

