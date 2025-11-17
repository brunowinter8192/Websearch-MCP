# CLAUDE.MD - MCP Server Engineering Reference

## WHO WE ARE

### You: The Storm
Critical software engineer. Relentless, precise, brutally intelligent.
Think 5 times before acting. Question everything. Ask when unclear.
Root causes, not symptoms. No assumptions.

### Me: The Observer
Extremely observant. Critical. I **will** notice everything.
Better to clarify now than rebuild later.

---

## CODE PRINCIPLES

**LEAN** | **SOLID** | **DRY** | **KISS** | **YAGNI**
Long-term thinking. Brutal honesty. No overengineering.

---

## PRIORITY LEVELS

**CRITICAL:** Must follow - violations break the system
**IMPORTANT:** Should follow - violations reduce quality
**RECOMMENDED:** Good practice - improves maintainability

---

## CRITICAL STANDARDS

- NO comments inside function bodies (only function header comments + section markers)
- NO test files in root (ONLY in debug/ folders - root or per-module)
- NO debug/ or logs/ folders in version control (MUST be in .gitignore)
- NO emojis in production code, READMEs, DOCS.md, logs
- NO verbose console output (use logging instead)

**Type hints:** RECOMMENDED but optional

**Fail-Fast:** Let exceptions fly. No try-catch that silently swallows errors affecting business logic. Script must fail if it cannot fulfill its purpose.

---

## MCP SERVER ARCHITECTURE

### Project Structure

**MCP with module domains:**
```
mcp_server/
├── server.py              # MCP server orchestrator (Tool definitions)
├── src/                   # Source modules package
│   ├── __init__.py        # Package marker (required for imports)
│   ├── domain_one/        # First domain (e.g., scraper, api_client)
│   │   ├── __init__.py
│   │   ├── tool_one.py    # Module for tool_one
│   │   ├── tool_two.py    # Module for tool_two
│   │   └── DOCS.md        # Documentation for this domain
│   └── domain_two/        # Second domain (e.g., config, storage)
│       ├── __init__.py
│       ├── settings.yml   # Configuration files
│       └── DOCS.md        # Documentation for this domain
├── README.md              # Quick start, installation, usage
├── CLAUDE.md              # Engineering standards
├── .mcp.json              # Claude Code MCP registration
├── docker-compose.yml     # Container configuration (if needed)
├── debug/                 # Debug scripts for testing (gitignored)
├── bug_fixes/             # Bug fix documentation (gitignored)
└── logs/                  # Log files (gitignored)
    └── server.log
```

**Key principle:** Each domain folder in src/ contains related modules plus its own DOCS.md. No central DOCS.md - documentation lives with the code it describes. Clean separation with package imports.

---

## server.py PATTERN

**CRITICAL:** server.py is the orchestrator. Only imports and tool definitions.

```python
# INFRASTRUCTURE
from typing import Annotated, Literal
from fastmcp import FastMCP
from pydantic import Field

from src.domain.tool_one import tool_one_workflow
from src.domain.tool_two import tool_two_workflow

mcp = FastMCP("ServerName")


# TOOLS

@mcp.tool
def tool_one(
    param: Annotated[str, Field(description="Parameter description with example")]
) -> dict:
    """Use when user asks for X. Good for Y, Z use cases."""
    return tool_one_workflow(param)


@mcp.tool
def tool_two(
    param: Annotated[str, Field(description="Parameter description")],
    option: Annotated[
        Literal["opt_a", "opt_b", "opt_c"],
        Field(description="Explain each option: opt_a (meaning), opt_b (meaning), opt_c (meaning)")
    ] = "opt_a"
) -> dict:
    """Use when user needs specific functionality. Helps with A, B scenarios."""
    return tool_two_workflow(param, option)


if __name__ == "__main__":
    mcp.run()
```

**Rules:**
- NO business logic in server.py
- Each tool delegates to module orchestrator
- All parameters use Annotated + Field
- Literal for enum-like choices with clear descriptions

---

## MODULE PATTERN (src/domain/tool_name.py)

**CRITICAL:** Each module follows INFRASTRUCTURE → ORCHESTRATOR → FUNCTIONS

```python
# INFRASTRUCTURE
import requests
from typing import Literal

API_BASE = "https://api.example.com"
RESULTS_LIMIT = 20


# ORCHESTRATOR
def tool_name_workflow(param: str, option: str = "default") -> dict:
    raw_data = fetch_data(param, option)
    return format_response(raw_data)


# FUNCTIONS

# Fetch data from external API
def fetch_data(param: str, option: str) -> dict:
    url = f"{API_BASE}/endpoint"
    response = requests.get(url, params={"q": param})
    response.raise_for_status()
    return response.json()


# Transform raw API response into clean output
def format_response(raw_data: dict) -> dict:
    return {
        "field_one": raw_data["nested"]["field"],
        "field_two": raw_data.get("optional", "")
    }
```

**Section definitions:**

**INFRASTRUCTURE:**
- Imports and constants
- NO functions
- NO logic

**ORCHESTRATOR:**
- ONE function (named: tool_name_workflow)
- Called by server.py tool definition
- Calls internal functions in sequence
- ZERO functional logic (only function composition)

**FUNCTIONS:**
- Ordered by call sequence
- One responsibility each
- Function header comment (one line describing WHAT)
- NO inline comments

---

## TOOL PARAMETER DESIGN

**CRITICAL:** Parameters must be intuitive for LLM understanding

### Two-Layer Documentation (NO DUPLICATION)

**Field Description** = Technical parameter details (what, how, format)
**Docstring** = Semantic use cases (when, why to use this tool)

```python
@mcp.tool
def search_repos(
    query: Annotated[str, Field(description="Search query with GitHub qualifiers (e.g., 'machine learning stars:>100 language:python')")],
    sort_by: Annotated[
        Literal["stars", "forks", "updated", "best_match"],
        Field(description="Sort results by: stars (popularity), forks, updated (recent activity), or best_match (relevance)")
    ] = "best_match"
) -> dict:
    """Use when user asks to find projects, libraries, frameworks on GitHub. Good for brainstorming, discovering alternatives, finding popular implementations."""
    return search_repos_workflow(query, sort_by)
```

**Field tells LLM:** "How do I fill this parameter?"
**Docstring tells LLM:** "When should I call this tool?"

### Annotated + Field Pattern
```python
param: Annotated[str, Field(description="Clear explanation with example")]
```

### Field Description Guidelines
1. **Explain format:** What structure does this parameter expect?
2. **Provide examples:** (e.g., 'octocat', 'src/main.py')
3. **Clarify options:** For Literal types, explain each option
4. **Show syntax:** For query parameters, show expected format

**Good:**
```python
query: Annotated[str, Field(description="Search query with qualifiers (e.g., 'machine learning stars:>100 language:python')")]
```

**Bad:**
```python
query: str  # No description, LLM guesses
```

### Docstring Guidelines
1. **Start with "Use when..."** - Clear trigger condition
2. **Describe user intent** - What is user trying to achieve?
3. **List use cases** - Brainstorming, finding examples, etc.
4. **NO parameter descriptions** - Already in Field

**Good:**
```python
"""Use when user needs specific code examples, implementation patterns, or wants to see how others solved a problem."""
```

**Bad:**
```python
"""Search code across GitHub repositories."""  # Too vague, no use case guidance
```

### Literal Types for Constrained Choices
```python
sort_by: Annotated[
    Literal["stars", "forks", "updated", "best_match"],
    Field(description="Sort results by: stars (popularity), forks (fork count), updated (recent activity), or best_match (relevance)")
] = "best_match"
```

**Rules:**
- Always explain what each option means
- Provide sensible defaults
- Keep options limited (3-5 max)

---

## TOOL OUTPUT DESIGN

**CRITICAL:** Output must enable direct tool chaining

### Return Structure
```python
{
    "total_count": 150,
    "items": [
        {
            "owner": "octocat",           # For direct API calls
            "repo": "Hello-World",        # For direct API calls
            "full_name": "octocat/Hello-World",
            "description": "My first repo",
            "stars": 1500,
            "html_url": "https://github.com/..."
        }
    ]
}
```

**Principles:**
- Include all fields needed for next tool call
- Avoid nested structures when possible
- Consistent field names across tools
- Human-readable + machine-parseable

### Large Response Handling
When responses exceed context limits:

```python
MAX_CHARS = 1000

def format_response(data: dict) -> dict:
    formatted = transform(data)

    if len(str(formatted)) > MAX_CHARS:
        truncated = truncate_to_safe_size(formatted)
        return {
            "data": truncated,
            "truncated": True,
            "warning": "Response truncated. Use pagination or filters to narrow results."
        }

    return {
        "data": formatted,
        "truncated": False,
        "warning": None
    }
```

---

## TOOL SEPARATION PRINCIPLE

**CRITICAL:** One tool = One responsibility. No multi-mode tools.

**BAD:**
```python
@mcp.tool
def search(
    query: str,
    search_type: Literal["repos", "code", "users"]  # Too complex
) -> dict:
    ...
```

**GOOD:**
```python
@mcp.tool
def search_repos(query: str) -> dict:
    ...

@mcp.tool
def search_code(query: str) -> dict:
    ...

@mcp.tool
def search_users(query: str) -> dict:
    ...
```

**Rationale:**
- LLM makes intuitive choice based on task
- No ambiguity about tool purpose
- Each tool has focused parameters
- Easier to maintain and test

---

## ERROR HANDLING

**IMPORTANT:** Fail-fast philosophy

### When to use try-catch
**ALLOWED:**
- Retry logic with exponential backoff
- Graceful degradation with explicit logging
- Resource cleanup (files, connections)
- Converting exceptions to domain errors

**PROHIBITED:**
- Silently swallowing errors
- Generic `except Exception: pass`
- Hiding failures that affect business logic

### API Error Pattern
```python
# Let requests handle HTTP errors
response = requests.get(url, headers=headers)
response.raise_for_status()  # Raises on 4xx/5xx
return response.json()
```

FastMCP handles exceptions and communicates errors to client.

---

## DOCUMENTATION STRUCTURE

### README.md (root level)
- Server name and one-liner
- Installation instructions
- Quick start (how to run server)
- Environment variables
- NO link to central DOCS.md (doesn't exist)

### DOCS.md (module level only)
Each domain folder in src/ has its own DOCS.md documenting its modules.

**Location:** src/domain_name/DOCS.md

**Content:**
- Documents ALL files in that domain folder
- Python modules with function descriptions
- Configuration files with purpose and settings
- NO project-wide structure (that's in README.md)

**Structure:**

```markdown
# Domain Name

One-liner describing this domain's purpose.

## module_one.py

**Purpose:** WHY this module exists
**Input:** What parameters it receives
**Output:** What structure it returns

### workflow_function()
Main orchestrator. Coordinates data fetching and formatting.

### helper_function()
Performs specific operation. Describes what it does.

## module_two.py

**Purpose:** WHY this module exists
**Input:** What parameters it receives
**Output:** What structure it returns

### workflow_function()
Main orchestrator for this module.

## settings.yml

**Purpose:** Configuration for this domain.

Prose description of settings. Explains each configuration section and its purpose.
```

**Rules:**
- DOCS.md lives in module directories, NOT in project root
- Documents only files in that specific directory
- Python modules: functions get ### headers
- Config files: prose description of purpose and settings
- Prose text only (no bullet lists)
- Describe WHAT not HOW

---

## CLAUDE CODE INTEGRATION (.mcp.json)

**CRITICAL:** Each MCP server needs .mcp.json for Claude Code registration.

### Structure
```json
{
  "mcpServers": {
    "server_name": {
      "command": "/absolute/path/to/venv/bin/fastmcp",
      "args": ["run", "/absolute/path/to/server.py"],
      "env": {
        "API_TOKEN": "${API_TOKEN}"
      }
    }
  }
}
```

### Rules

**CRITICAL:**
- ALL paths MUST be absolute (no relative paths)
- command: Absolute path to fastmcp executable in venv
- args: ["run", "/absolute/path/to/server.py"]
- NO cwd field (unreliable in Claude Code)

**BAD:**
```json
{
  "args": ["run", "server.py"],
  "cwd": "/path/to/project"
}
```

**GOOD:**
```json
{
  "args": ["run", "/full/path/to/server.py"]
}
```

**Environment Variables:**
- Use ${VAR_NAME} syntax for secrets
- Never hardcode tokens/keys
- Optional field if no env vars needed

**Verification:**
```bash
claude mcp list
```

---

## NAMING CONVENTIONS

**server.py:** Always named server.py
**Domain folders:** src/domain_name/ (snake_case, descriptive)
**Modules:** src/domain/tool_name.py (snake_case, matches tool name)
**Package markers:** src/__init__.py and src/domain/__init__.py (required for imports)
**Orchestrator function:** tool_name_workflow()
**MCP tool function:** @mcp.tool def tool_name()
**Documentation:** src/domain/DOCS.md (one per domain)

**Examples:**
- src/scraper/search_web.py → search_web_workflow() → @mcp.tool def search_web()
- src/scraper/scrape_urls.py → scrape_urls_workflow() → @mcp.tool def scrape_urls()
- src/searxng/settings.yml → configuration for SearXNG instance

---

## COMPLIANCE

Scripts in `debug/` folders (root-level or per-module) are exempt from CLAUDE.md compliance requirements.

All other code must follow these standards strictly.
