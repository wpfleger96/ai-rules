# Project-Specific Configurations

Configure AI agent rules per-project. Each project gets its own `AGENTS.md` with project-specific rules that supplement user-level rules.

## Quick Start

1. Create project directory and config:
   ```bash
   mkdir config/projects/my-project
   cp config/projects/example-project/AGENTS.md config/projects/my-project/AGENTS.md
   # Edit config/projects/my-project/AGENTS.md with your rules
   ```

2. Add project to `~/.ai-rules-config.yaml`:
   ```yaml
   projects:
     my-project:
       path: ~/Development/my-project
       exclude_symlinks: []  # Optional
   ```

3. Install: `ai-rules install`

This creates symlinks in your project:
- `<project>/CLAUDE.md` → `config/projects/<name>/AGENTS.md`
- `<project>/.goosehints` → `config/projects/<name>/AGENTS.md`

## Configuration Options

```yaml
projects:
  my-api:
    path: ~/Development/work/my-api
    exclude_symlinks: [".goosehints"]  # Skip specific agents
```

**Options:**
- `path` - Required. Absolute or `~` relative path to project directory
- `exclude_symlinks` - Optional. Skip specific symlinks (e.g., `CLAUDE.md`, `.goosehints`)

**Exclusion behavior:** Global exclusions (from root config) apply everywhere. Project exclusions only apply to that project. See main README for details.

## Commands

Use `ai-rules --help` for full command reference. Key commands:
- `ai-rules list-projects` - Show all projects
- `ai-rules install --projects my-api` - Install specific project
- `ai-rules status` - Check all configurations
