# AI Assistants Handoff System

This repository implements a communication and handoff system between AI assistants.

## Components

- **`shared/schema.md`** - Defines the handoff message schema
- **`jules_runner.py`** - Handoff automation poller for Jules
- **`shared/`** - Communication directory for message exchange

## Usage

### Running the Handoff Poller

```bash
# Run continuous poller (checks every 10 seconds)
python jules_runner.py

# Check for messages once and exit
python jules_runner.py --check-once
```

### Message Format

Messages follow the schema defined in `shared/schema.md`:

```yaml
---
id: 2025-07-01T14:32:10Z
from: cc
for: jules
action: add_file
payload:
  path: example.txt
  contents: |
    Example file content
---

Optional markdown body content here.
```

### Supported Actions

- **`add_file`** - Create files in the workspace
- **`run_task`** - Execute tasks (acknowledged for now)
- **`message`** - General communication

## Architecture

1. **Claude Code** writes messages to `shared/claude-to-jules-message.md`
2. **Jules runner** processes messages and writes responses to `shared/jules-to-cc.md`
3. Processed messages are archived with timestamps
4. The system uses YAML frontmatter for structured data

## Environment

The system expects `ASSISTANT_PROJECT_ROOT` to be set to the workspace directory.
Bootstrap script ensures proper environment setup.
