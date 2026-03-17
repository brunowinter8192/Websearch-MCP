# Source Modules

Python packages for web search and scraping. Utility script for spawning Claude Code workers.

## tmux_spawn.sh

(from `src/spawn/`)

**Purpose:** Shell library for spawning Claude Code sessions in named tmux windows with an attached Ghostty terminal viewer. Supports both inline prompt and file-based prompt to avoid shell escaping issues.
**Input:** Sourced as a shell library (`source src/spawn/tmux_spawn.sh`), then called as functions.
**Output:** tmux pane ID on success; Ghostty window attached to the session.

### Functions

- `spawn_claude_worker SESSION NAME PROJECT_PATH MODEL TASK_PROMPT [EXTRA_FLAGS]` — Creates a new tmux window, waits for shell ready, launches `claude --model MODEL TASK_PROMPT` in the specified project directory, opens Ghostty viewer attached to the session. Returns pane ID.
- `spawn_claude_worker_from_file SESSION NAME PROJECT_PATH MODEL PROMPT_FILE [EXTRA_FLAGS]` — Like `spawn_claude_worker` but reads the task prompt from a file. Avoids shell escaping issues with complex multi-line prompts.
- `open_tmux_viewer SESSION [WINDOW_NAME]` — Opens a Ghostty window attached to a tmux session. Ghostty 1.3+: uses native AppleScript API. Ghostty 1.2.x: falls back to `open -na`.

### Usage

```bash
source src/spawn/tmux_spawn.sh
pane=$(spawn_claude_worker "workers" "my-task" "/path/to/project" "sonnet" "Fix the bug in foo.py")
pane=$(spawn_claude_worker_from_file "workers" "my-task" "/path/to/project" "opus" "/tmp/prompt.txt")
```

## Documentation Tree

- [scraper/DOCS.md](scraper/DOCS.md) — URL scraping and site exploration tools
- [searxng/DOCS.md](searxng/DOCS.md) — SearXNG API wrapper and configuration
