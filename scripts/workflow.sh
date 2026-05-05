#!/usr/bin/env zsh

# === Workflow Manager ===
# Installed by workflow-manager project
# Source: scripts/workflow.sh

# === Tool Selection ===
# Primary:   claude   (Claude Code CLI — Claude Pro)
# Secondary: codex                  (Codex CLI — when preserving Claude quota or need GPT)
# Optional:  antigravity IDE        (if more Claude Sonnet quota needed)
# Optional:  gemini                 (if Gemini quota available via Cockpit)
#
# Agent context files per project:
#   AGENTS.md   → Codex CLI, Antigravity IDE (source of truth)
#   CLAUDE.md   → Claude Code CLI (mirror — do not edit directly)
#   GEMINI.md   → Gemini CLI, Antigravity IDE (mirror — do not edit directly)
#
# To sync: edit AGENTS.md in any project, then run: project-sync

WORKFLOW_SCRIPT_SOURCE="${${(%):-%x}:A}"
WORKFLOW_MANAGER_HOME="${WORKFLOW_MANAGER_HOME:-${WORKFLOW_SCRIPT_SOURCE:h:h}}"
WORKFLOW_OPEN_CMD="${WORKFLOW_OPEN_CMD:-open}"
typeset -ga WORKFLOW_ROOTS
typeset -ga WORKFLOW_ROOT_ARGS
typeset -ga WORKFLOW_CONFIGURED_ROOTS
typeset -ga WORKFLOW_EXISTING_ROOTS
typeset -g WORKFLOW_ROOT_SOURCE


workflow() {
  command python3 "$WORKFLOW_MANAGER_HOME/bin/workflow" "$@"
}

_workflow_open_file() {
  local path="$1"
  if [ -z "$path" ]; then
    return 0
  fi
  command "$WORKFLOW_OPEN_CMD" "$path"
}

_workflow_prepare_roots() {
  WORKFLOW_ROOT_ARGS=()
  WORKFLOW_CONFIGURED_ROOTS=()
  WORKFLOW_EXISTING_ROOTS=()
  WORKFLOW_ROOT_SOURCE="$WORKFLOW_MANAGER_HOME/.workflow/roots.json"

  if [ "${#WORKFLOW_ROOTS[@]}" -gt 0 ]; then
    WORKFLOW_ROOT_SOURCE="temporary WORKFLOW_ROOTS override"
    local root
    for root in "${WORKFLOW_ROOTS[@]}"; do
      WORKFLOW_ROOT_ARGS+=(--roots "$root")
      WORKFLOW_CONFIGURED_ROOTS+=("$root")
      if [ -d "$root" ]; then
        WORKFLOW_EXISTING_ROOTS+=("$root")
      fi
    done
    return 0
  fi

  local roots_payload
  roots_payload=$(workflow roots --format shell) || return 1
  eval "$roots_payload"
  if [ -n "$WORKFLOW_ROOTS_CONFIG" ]; then
    WORKFLOW_ROOT_SOURCE="$WORKFLOW_ROOTS_CONFIG"
  fi
}

# Find project matches by name across the configured roots
_workflow_find_project_matches() {
  local name="$1"
  local found=1
  local root
  for root in "${WORKFLOW_CONFIGURED_ROOTS[@]}"; do
    if [ -d "$root/$name" ]; then
      echo "$root/$name"
      found=0
    fi
  done
  return "$found"
}

# Open or create a project
project-open() {
  if [ -z "$1" ]; then
    echo "Usage: project-open <project-name> [--root /absolute/path]"
    echo ""
    echo "Available projects:"
    project-list
    return 1
  fi

  local name="$1"
  shift
  local chosen_root=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --root)
        if [ -z "$2" ]; then
          echo "Error: --root requires an absolute path."
          return 1
        fi
        chosen_root="$2"
        shift 2
        ;;
      *)
        echo "Error: unknown argument '$1'"
        echo "Usage: project-open <project-name> [--root /absolute/path]"
        return 1
        ;;
    esac
  done

  _workflow_prepare_roots || return 1

  local -a matches
  matches=()
  local match
  while IFS= read -r match; do
    [ -n "$match" ] && matches+=("$match")
  done < <(_workflow_find_project_matches "$name")

  local open_payload
  if [ "${#matches[@]}" -gt 1 ]; then
    echo "Error: project '$name' exists in multiple roots."
    for match in "${matches[@]}"; do
      echo "  - $match"
    done
    return 1
  fi

  if [ "${#matches[@]}" -eq 1 ]; then
    open_payload=$(workflow open "$name" "${WORKFLOW_ROOT_ARGS[@]}" --format shell) || return 1
  else
    echo ""
    echo "Project '$name' not found in any known folder."
    if [ -z "$chosen_root" ]; then
      if [ "${#WORKFLOW_EXISTING_ROOTS[@]}" -eq 0 ]; then
        echo "Error: no existing workspace roots are available for creation."
        echo "Pass --root /absolute/path or update $WORKFLOW_ROOT_SOURCE."
        return 1
      fi
      echo "Where should it live?"
      echo ""
      local i=1
      local root
      for root in "${WORKFLOW_EXISTING_ROOTS[@]}"; do
        echo "  $i) $root"
        ((i++))
      done
      echo ""
      printf "Enter number (or press Enter to cancel): "
      local choice
      read choice
      if [ -z "$choice" ]; then
        echo "Cancelled."
        return 1
      fi
      chosen_root="${WORKFLOW_EXISTING_ROOTS[$choice]}"
    fi
    if [ -z "$chosen_root" ]; then
      echo "Invalid choice."
      return 1
    fi
    open_payload=$(workflow open "$name" "${WORKFLOW_ROOT_ARGS[@]}" --create --root "$chosen_root" --format shell) || return 1
  fi

  eval "$open_payload"

  if [ -n "$WORKFLOW_OPEN_CREATED" ]; then
    echo ""
    echo "Created new v2 project: $name"
    echo "Root: $chosen_root"
    echo ""
  fi

  cd "$WORKFLOW_OPEN_PATH" || return 1
  workflow status
}

# Close current project — prompts state update
project-close() {
  local close_payload
  close_payload=$(workflow close --format shell "$@") || return 1
  eval "$close_payload"

  if [ -n "$WORKFLOW_CLOSE_OPEN_PATH" ]; then
    _workflow_open_file "$WORKFLOW_CLOSE_OPEN_PATH"
  fi

  workflow close "$@"
}

# Confirm state is saved — lightweight close confirmation
project-save() {
  workflow save "$@"
}

# List all projects across known roots
project-list() {
  _workflow_prepare_roots || return 1
  workflow list "${WORKFLOW_ROOT_ARGS[@]}"
}

# Show current project state
project-status() {
  workflow status "$@"
}

# Add a new project root folder
project-add-root() {
  if [ -z "$1" ]; then
    echo "Usage: project-add-root /absolute/path/to/folder"
    return 1
  fi
  echo ""
  echo "To permanently add a new root, edit:"
  echo "$WORKFLOW_MANAGER_HOME/.workflow/roots.json"
  echo ""
  echo "Add your path to the roots array, then validate with:"
  echo "workflow roots --validate"
  echo ""
  echo "This repo does not edit shell startup files automatically."
}

# Re-initialise scaffold files in an existing project (non-destructive)
project-init() {
  workflow init "$@"
}

project-sync() {
  workflow sync "$@"
}

workflow-doctor() {
  workflow doctor "$@"
}
