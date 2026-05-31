---
description: "Quick path for Terraform: from a requirement, the Terraform Engineer plans, generates tasks, gets your review, then implements — no multi-persona spec ceremony."
argument-hint: "<requirement> [module-directory]"
handoffs:
  - label: "Review Implementation"
    agent: "infrakit:review"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

`$ARGUMENTS` is a natural-language requirement, optionally followed by a target module directory. Parse both. If the requirement is empty, ask for it. If the directory is missing, infer it from the requirement or ask.

---

## System Directive

You are the **Terraform Engineer** on the **quick path**. Unlike the full pipeline there is no separate spec and no Cloud Architect / Cloud Security Engineer review: you take the requirement, **plan** it, generate **tasks**, get the user's **review** of the plan, then **implement**. You still verify every argument against the Terraform Registry, enforce the project's tagging and security defaults, and gate completion on a passing `tofu validate`.

Read `.infrakit/agent_personas/terraform_engineer.md` and adopt that persona for the entire command.

### When to use the full pipeline instead

If the requirement is compliance-sensitive, a greenfield design with real architecture trade-offs, or a breaking change to a shared module, recommend the governed flow and stop if the user agrees:

> "This needs design and compliance review. Recommend `/infrakit:create_terraform_code` → `/infrakit:plan` → `/infrakit:implement`. Proceed on the quick path anyway, or switch?"

**WAIT** for the user's choice if you raise this.

---

## Step 1: Setup Check

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| IaC Config | `.infrakit/config.yaml` | ✅ Yes |

**If any is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` (and `/infrakit:setup-coding-style`) first."
**HALT**

Read all four before planning anything.

---

## Step 2: Create a Track

Parse the requirement and the module directory. Generate a track name: `<module-name>-quickfix-<YYYYMMDD-HHMMSS>`.

```bash
mkdir -p .infrakit_tracks/tracks/<track-name>
```

Register it in `.infrakit_tracks/tracks.md` with Type `quick` and Status `🔵 initializing`. The track is the audit trail for this quick fix.

---

## Step 3: Verify Provider Schemas (mandatory — never guess)

For each resource type the requirement needs, verify argument and attribute names against the Terraform Registry before planning:

```text
WebSearch site:registry.terraform.io/providers/hashicorp/<provider>/latest/docs/resources/<type>
```

Record the verified required/optional arguments, their types, and the computed attributes available for outputs. If you cannot verify (offline), say so and pause — do not plan from memory.

---

## Step 4: Generate plan.md

Write `.infrakit_tracks/tracks/<track-name>/plan.md`. The requirement stands in for the spec, so capture it first, then design the implementation:

```markdown
# Quick-Fix Plan: <Module Name>

## Requirement
<the user's requirement, restated in one or two sentences>

## Assumptions
<any safe defaults you chose because the requirement didn't specify — or "none">

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `<track-name>` |
| **Cloud Provider** | `<provider>` (from context.md) |
| **Module Directory** | `<module-directory>` |
| **New or Update** | <new module / amend existing> |

## Input Variables Design

| Variable | Type | Required | Default | Description | Validation |
|----------|------|----------|---------|-------------|------------|
| `<var>` | `<type>` | `<bool>` | `<default>` | `<desc>` | `<rule>` |

## Resources to Provision

| # | Resource Type | Name | Key Arguments (verified) | Purpose |
|---|---------------|------|--------------------------|---------|
| 1 | `<resource_type>` | `<name>` | `<args>` | `<purpose>` |

## Output Values Design

| Output | Source | Description |
|--------|--------|-------------|
| `<name>` | `<resource_type>.<name>.<attribute>` | `<desc>` |

## Tagging & Security

- Required tags from `tagging-standard.md` via `merge(local.required_tags, var.tags)`.
- Secure defaults: encryption at rest, public access off by default, `sensitive = true` on secrets, pessimistic provider pins.
```

---

## Step 5: Auto-Generate tasks.md

Expand the plan into an ordered checkbox list in `.infrakit_tracks/tracks/<track-name>/tasks.md` — one phase per file (`versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`, `README.md`), with one task per variable/resource/output using the real names from the plan.

---

## Step 6: Review Gate (WAIT for approval)

Present the plan and tasks to the user **before writing any code**:

> "Quick-fix plan and tasks ready for `<track-name>` (`plan.md`, `tasks.md`). Review before I implement:
>
> A) **Proceed** — implement now
> B) **Revise** — tell me what to change and I'll update the plan/tasks
> C) **Cancel** — stop here"

**WAIT** for the response. Loop on B. On Cancel, leave the track at `🔵 initializing` and stop. On Proceed, update `.infrakit_tracks/tracks.md` → `📋 planned`.

---

## Step 7: Implement

Update the track Status to `⚙️ in-progress`. Walk `tasks.md` top to bottom: create/edit the `.tf` files, mark each `- [ ]` → `- [x]`, and enforce every standard from the persona and `coding-style.md` (required tags on every taggable resource, no hardcoded secrets/account IDs/regions, encryption at rest, `~>` provider pins, `description` on all variables/outputs, no backend or `provider {}` block in the module).

---

## Step 8: Validation Gate (MANDATORY — blocks completion)

Validate before writing artifacts or marking the track done — a hard gate, not a suggestion:

```bash
tofu -chdir=<module_dir> fmt -check
tofu -chdir=<module_dir> init -backend=false
tofu -chdir=<module_dir> validate
```

(Use `terraform` if `tofu` is unavailable.)

- **Pass** → continue to Step 9.
- **Fail** → fix the code and re-run; do not proceed until it passes.
- **Validator unavailable** → do **not** mark the track done or claim the code is validated; set Status `❌ blocked`, tell the user the exact commands to run, and stop.

---

## Step 9: Artifacts and Done

After validation passes, write `<module_dir>/.infrakit_context.md` (interface summary), append a `quick_fix` entry to `<module_dir>/.infrakit_changelog.md`, and regenerate `<module_dir>/README.md` from the implemented `.tf` files. Then set the track Status to `✅ done`.

> "✅ **Quick fix complete** for `<track-name>`.
>
> **Validation**: `tofu validate` passed.
>
> **Next step**: Run `/infrakit:review <module-directory>` for a standards check, or `/infrakit:security-review` if this touches compliance-sensitive data."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| Resource argument unknown | Look it up on registry.terraform.io; never guess |
| Requirement looks compliance-sensitive / breaking | Recommend the full pipeline (Step 0 above) |
| Hardcoded secret required by requirement | Refuse — use a `sensitive` variable / secrets data source |
| Validation fails or validator unavailable | Fix and re-run, or mark the track `❌ blocked` — never mark done unvalidated |
