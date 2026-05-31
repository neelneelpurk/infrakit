# Installation Guide

## Prerequisites

- Linux, macOS, or Windows
- A [supported AI agent](../README.md#supported-ai-agents) (Claude Code, Gemini CLI, GitHub Copilot, Cursor, etc.)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- `kubectl` (for Crossplane projects)
- `terraform` (for Terraform projects)
- `aws` CLI, and optionally `cfn-lint` (for CloudFormation projects)

---

## Installation

### Option 1: Persistent Installation (Recommended)

Install `infrakit-cli` as a persistent tool using `uv`:

```bash
uv tool install infrakit-cli --from git+https://github.com/neelneelpurk/infrakit.git
```

Then initialize your project:

```bash
# New project directory
infrakit init my-infra --ai claude --iac crossplane

# Or initialize in the current directory
infrakit init --here --ai claude --iac crossplane
```

### Option 2: One-Time Usage

Run without installing using `uvx`:

```bash
uvx --from git+https://github.com/neelneelpurk/infrakit.git infrakit init my-infra --ai claude --iac crossplane
```

---

## Choosing Your AI Agent

Specify your agent with `--ai`:

```bash
infrakit init my-infra --ai claude --iac crossplane
infrakit init my-infra --ai codex --iac crossplane
infrakit init my-infra --ai gemini --iac crossplane
infrakit init my-infra --ai copilot --iac crossplane
```

For a full list of supported agents see [Supported AI Agents](../README.md#supported-ai-agents).

**Bring your own agent:**

```bash
infrakit init my-infra --ai generic --ai-commands-dir .myagent/commands/ --iac crossplane
```

---

## Verification

After initialization, verify these command files are installed in your agent's commands directory:

```bash
# Claude Code
ls .claude/commands/ | grep infrakit

# Gemini CLI
ls .gemini/commands/ | grep infrakit

# GitHub Copilot
ls .github/prompts/ | grep infrakit
```

You should see the following commands available in your AI agent:

**Generic (shared by every IaC tool):**
- `/infrakit:setup` — Configure project context and tagging requirements
- `/infrakit:setup-coding-style` — Configure IaC coding-style standards
- `/infrakit:status` — Track progress dashboard
- `/infrakit:analyze` — Spec/plan/code consistency check
- `/infrakit:architect-review` — Architecture review
- `/infrakit:security-review` — Security compliance review

**Shared workflow (per IaC tool):**
- `/infrakit:plan` — Generate the implementation plan and auto-generate `tasks.md`
- `/infrakit:implement` — Execute the tasks in `tasks.md`
- `/infrakit:review` — Code review against coding standards
- `/infrakit:quick_fix` — Fast path: IaC Engineer writes/updates code directly

**Crossplane:**
- `/infrakit:new_composition` — Multi-persona new resource workflow
- `/infrakit:update_composition` — Update an existing composition

**Terraform:**
- `/infrakit:create_terraform_code` — Multi-persona new resource workflow
- `/infrakit:update_terraform_code` — Update an existing module

**CloudFormation:**
- `/infrakit:create_cloudformation_code` — Multi-persona new resource workflow
- `/infrakit:update_cloudformation_code` — Update an existing template

---

## Initial Project Configuration

After initialization, run `/infrakit:setup` in your AI agent to configure:

1. **Project context** — cloud provider, API groups, naming conventions, environments
2. **Coding standards** — Pipeline mode requirements, connection secrets, patch patterns
3. **Tagging requirements** — required tags, enforcement rules, provider-specific field paths

```text
/infrakit:setup
```

`/infrakit:setup` writes `.infrakit/context.md` and `.infrakit/tagging-standard.md`; `/infrakit:setup-coding-style` fills in `.infrakit/coding-style.md`. Together these are the files that all InfraKit commands read before generating or reviewing code.

---

## Troubleshooting

### Git Credential Manager on Linux

```bash
#!/usr/bin/env bash
set -e
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
git config --global credential.helper manager
rm gcm-linux_amd64.2.6.1.deb
```

### Slash commands not appearing

1. Verify command files exist in the expected directory (see Verification above)
2. Restart your AI agent or IDE completely
3. Re-run `infrakit init --here --force --ai <your-agent> --iac crossplane` to refresh files
