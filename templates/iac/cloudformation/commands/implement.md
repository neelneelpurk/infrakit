---
description: "Execute the implementation plan for a CloudFormation track by working through all tasks in tasks.md."
argument-hint: "<track-name>"
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

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to implement?
> Example: `s3-secure-bucket-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **CloudFormation Engineer** executing the implementation for an infrastructure track. Work through the tasks in `tasks.md` one by one, marking each complete as you go.

Read `.infrakit/agent_personas/cloudformation_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required configuration files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| IaC Config | `.infrakit/config.yaml` | ✅ Yes |

**If any setup file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

---

## Step 2: Verify Track Files

Verify the track has all required artifacts:

| File | Path | Required |
|------|------|----------|
| Spec | `.infrakit_tracks/tracks/<track-name>/spec.md` | ✅ Yes |
| Plan | `.infrakit_tracks/tracks/<track-name>/plan.md` | ✅ Yes |
| Tasks | `.infrakit_tracks/tracks/<track-name>/tasks.md` | ✅ Yes |

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:create_cloudformation_code` or `/infrakit:update_cloudformation_code` first."
**HALT**

**If plan.md is missing:**
> "❌ `plan.md` not found. Run `/infrakit:plan <track-name>` first."
**HALT**

**If tasks.md is missing:**
> "❌ `tasks.md` not found. `tasks.md` is generated automatically by `/infrakit:plan`. Run `/infrakit:plan <track-name>` to regenerate it."
**HALT**

---

## Step 3: Load Standards and Adopt Persona

Read these files before writing any code:

- `.infrakit/coding-style.md` — **MANDATORY**: all template content must follow these standards exactly
- `.infrakit/tagging-standard.md` — **MANDATORY**: all taggable resources must include required tags
- `.infrakit/agent_personas/cloudformation_engineer.md` — detailed persona behavior (if present)

> "Adopting the **CloudFormation Engineer** persona for implementation."

---

## Step 4: Load Track Artifacts

Read all track files:

1. `.infrakit/context.md` — AWS account structure, regions, naming conventions
2. `.infrakit_tracks/tracks/<track-name>/spec.md` — What to build (parameters, outputs, security requirements)
3. `.infrakit_tracks/tracks/<track-name>/plan.md` — File structure, resource mappings, tagging strategy
4. `.infrakit_tracks/tracks/<track-name>/tasks.md` — Ordered task list

---

## Step 5: Present Task Summary and Set Status

Update `.infrakit_tracks/tracks.md` — change the track's Status to `⚙️ in-progress`.

Before starting, display the task summary:

> "**Starting implementation for track**: `<track-name>`
>
> | Metric | Value |
> |--------|-------|
> | Total Tasks | N |
> | Already Completed | N |
> | Remaining | N |
>
> Beginning implementation..."

---

## Step 6: Execute Tasks

**For each incomplete task (lines matching `- [ ]`) in tasks.md:**

1. Read the task description carefully
2. Execute the task — create or edit `template.yaml` (and example parameter files)
3. After completing, mark it done in tasks.md: change `- [ ]` to `- [x]`
4. Report: "✅ Task `<ID>` complete: `<task description>`"

**Task execution rules:**

- Execute tasks **in order** unless marked `[P]` (parallel-safe)
- `[P]` tasks touch different files and can run together
- If a task fails: report the error clearly, HALT, and ask the user how to proceed
- Do not skip tasks without explicit user approval
- **Verify each resource type and property against the AWS docs before writing it** — never guess a property name

---

## Step 7: Coding Standards Enforcement

**MANDATORY** — apply to every resource written:

- Follow all patterns in `.infrakit/coding-style.md` exactly
- Apply all required tags from `.infrakit/tagging-standard.md` to every taggable resource
- Never hardcode secrets, passwords, or API keys — use `NoEcho` parameters and dynamic references (`{{resolve:secretsmanager:...}}`, `{{resolve:ssm-secure:...}}`)
- Never hardcode account IDs, regions, or ARNs the pseudo parameters provide (`AWS::AccountId`, `AWS::Region`, `AWS::Partition`, `AWS::StackName`)
- Never default open ingress or public access — gate any exposure behind a `Parameter` + `Condition`
- Always enable encryption at rest for storage resources
- Always set `DeletionPolicy` / `UpdateReplacePolicy` on stateful resources per environment
- Every parameter and output must have a `Description`

If a task appears to conflict with coding standards, flag it **before** writing:

> "⚠️ This task conflicts with coding-style.md: `<explain conflict>`. How would you like to proceed?"

**WAIT** for response before continuing.

---

## Step 8: Validation Gate (MANDATORY — blocks completion)

After all tasks are marked `[x]`, you **MUST** validate the template before writing any artifacts (Step 9) or marking the track done (Step 10). This is a hard gate, not a suggestion: InfraKit's promise is *schema-verified* output. `cfn-lint` is the check that catches a hallucinated resource type or property name — exactly the class of error this gate exists for.

Run, from the template directory:

```bash
cfn-lint template.yaml
aws cloudformation validate-template --template-body file://template.yaml   # if credentials available
```

- **`cfn-lint` passes** → continue to Step 9.
- **`cfn-lint` fails** → fix the template and re-run. Do **not** proceed until it passes.
- **`cfn-lint` not installed** → fall back to a YAML syntax check (`python3 -c "import yaml; yaml.safe_load(open('template.yaml'))"`). The syntax check must pass, but it does **not** verify resource types/properties — say so explicitly in the summary and recommend installing `cfn-lint`. Do not imply schema-level validation you didn't run. If even the YAML parse fails, mark the track ❌ blocked.

Once validation passes:

> "✅ All tasks complete and validation passes for track `<track-name>` (cfn-lint: <ran/skipped>).
>
> **Next step**: Run `/infrakit:review <template-directory>` to review the implementation against coding standards."

---

## Step 9a: Update .infrakit_context.md

After the review is approved, generate or update `.infrakit_context.md` in the template directory:

```markdown
# InfraKit Context: <template-name>

**Purpose**: <one-line description of what this template provisions>
**Track**: `<track-name>` | **Completed**: <YYYY-MM-DD>
**Template**: `<template-directory>/template.yaml`

## Parameters

| Parameter | Type | Default | NoEcho | Description |
|-----------|------|---------|--------|-------------|
| <name> | <type> | <default> | <yes/no> | <desc> |

## Outputs

| Output | Value | Exported | Description |
|--------|-------|----------|-------------|
| <name> | `!GetAtt <LogicalId>.<attr>` | <yes/no> | <desc> |

## Resources Provisioned

| Logical ID | Type | DeletionPolicy | Purpose |
|------------|------|----------------|---------|
| `<LogicalId>` | `<AWS::Service::Type>` | `<policy>` | <purpose> |
```

---

## Step 9b: Update .infrakit_changelog.md

Append a new entry to `<template_directory>/.infrakit_changelog.md`.

If the file does not exist, create it with a header first:

```markdown
# InfraKit Changelog: <template-name>

<!-- Appended automatically by /infrakit:implement after each successful implementation. -->
```

Then append:

```markdown
## <track-name> — <YYYY-MM-DD>

**Change Type**: <Additive/Behavioral/Breaking/Mixed — from spec.md Change Overview>
**Summary**: <one-line summary from spec.md>

### Changes Implemented
- ADD: <from spec ADD table, or "none">
- MODIFY: <from spec MODIFY table, or "none">
- REMOVE: <from spec REMOVE table, or "none">

**Stack-Update Impact**: <No-interruption / Some-interruption / Replacement — from spec.md Architecture Decision>
**Spec**: `.infrakit_tracks/tracks/<track-name>/spec.md`
```

---

## Step 9c: Update README.md

Re-read the freshly-written `template.yaml` and regenerate `<template_directory>/README.md` to reflect the actual implemented state.

The template's `README.md` is both the user-facing usage doc and the human-readable interface contract. It must include:

- A one-paragraph description of what the template provisions.
- A **Deploy** section with a complete `aws cloudformation deploy --template-file template.yaml --stack-name <name> --parameter-overrides ...` example showing the minimum required parameters.
- A **Parameters** table — name, type, default, description — sourced from `template.yaml`.
- An **Outputs** table — name, description, exported — sourced from `template.yaml`.
- A **Validation** section with the commands a reviewer can run locally (`cfn-lint template.yaml`, `aws cloudformation validate-template`).

If `README.md` already exists, **regenerate** it rather than patching — the implementation is the source of truth, the README must match.

Present the regenerated README to the user:

> "I've regenerated `README.md` to match the implementation. Please review:
>
> <summary of key changes: parameters added/removed, outputs added/removed, examples updated>
>
> A) **Accept** — README looks correct
> B) **Edit manually** — Say 'done' when you've finished editing"

**WAIT** for response before proceeding to Step 10.

> **Note**: InfraKit does not generate a separate contract file — `template.yaml` is the machine-readable interface contract, and `README.md` is the human-readable one. Together they cover what a contract file used to.

---

## Step 10: Update Track Registry

Only mark the track ✅ done if the Step 8 validation gate **passed**. If validation could not run or failed, set the status to ❌ blocked instead and surface why — never mark an unvalidated template as done.

Update `.infrakit_tracks/tracks.md` — change the track's status to `✅ done`.

> "✅ **Implementation complete!**
>
> **Track**: `<track-name>`
> **Status**: done
>
> **Template files updated:**
> - `<template_directory>/template.yaml`
> - `<template_directory>/.infrakit_context.md`
> - `<template_directory>/.infrakit_changelog.md`
> - `<template_directory>/README.md`
>
> Run `/infrakit:status` to see all track statuses."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:create_cloudformation_code` or `/infrakit:update_cloudformation_code` |
| plan.md missing | Halt, direct to `/infrakit:plan <track-name>` |
| tasks.md missing | Halt, direct to `/infrakit:plan <track-name>` (plan auto-generates tasks.md) |
| Task execution fails | Report error, halt, ask user how to proceed |
| Coding style conflict | Flag before writing, wait for user |
| Hardcoded secret detected | Refuse — move to a `NoEcho` parameter or dynamic reference |
