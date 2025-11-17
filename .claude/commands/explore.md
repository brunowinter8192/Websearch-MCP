---
description: Explore codebase with search specialist agent (Haiku)
argument-hint: [question] | [reason why you need this]
---

# Codebase Exploration

You have received an exploration request from the user.

**Full Input:** $ARGUMENTS

## Parse the Input

The user provides:
- **Question**: What they want to find/understand (before the `|`)
- **Reason**: Why they need this information (after the `|`)

If no `|` separator is provided, treat the entire input as the question and infer the reason from context.

## Your Task

1. **Parse** the question and reason from the input
2. **Launch** the `explore-specialist` subagent using the Task tool
3. **Wait** for the agent's search report
4. **Present** the findings to the user in a clear, actionable format

## Execute

Use the Task tool to launch the explore-specialist agent:

```
Tool: Task
Parameters:
  description: "Explore codebase"
  subagent_type: "explore-specialist"
  model: "haiku"
  prompt: |
    ## Exploration Request

    **Question:** [extracted question]

    **Reason/Goal:** [extracted reason]

    Please search the codebase systematically and provide a structured report with:
    - Direct answer to the question
    - Relevant file paths with line numbers
    - Key code patterns found
    - Context specific to the stated goal
```

## After Receiving Report

Present the findings to the user:
- Summarize key discoveries
- Highlight the most relevant files (with clickable paths)
- Provide actionable next steps based on their reason

The explore-specialist uses Haiku for fast, efficient searches. The report will contain file:line references that help the user navigate directly to relevant code.
