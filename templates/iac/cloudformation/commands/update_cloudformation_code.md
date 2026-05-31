---
description: "Update an existing AWS CloudFormation template through a multi-persona review workflow."
argument-hint: "<template-directory>"
handoffs:
  - label: "Generate Plan"
    agent: "infrakit:plan"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

Parse `$ARGUMENTS` for the template directory. If not provided, ask.

---

## System Directive

You are guiding the user through updating an existing AWS CloudFormation template. This command scans the existing template to understand the current state, ensures all template context files are present and reviewed, then runs a structured solutioning and review workflow.

CloudFormation is AWS-only — do not ask which cloud provider.

**CRITICAL**: Ask only one question at a time. Wait for a response before asking the next.

---

## Phase 1: Setup Check

### 1.1 Verify Required Files

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| Track Registry | `.infrakit_tracks/tracks.md` | ✅ Yes |

**If any file is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` to initialize."
**HALT**

Read `.infrakit/context.md`, `.infrakit/coding-style.md`, and `.infrakit/tagging-standard.md` before proceeding.

---

## Phase 2: Argument Collection and Validation

### 2.1 Template Directory

If not provided in `$ARGUMENTS`, ask:

> "Which template directory do you want to update?
>
> Example: `./templates/s3-secure-bucket`"

**WAIT** for response.

### 2.2 Validate Directory Exists and Contains a Template

```bash
test -d <template_directory>
```

**If directory does NOT exist:**
> "❌ Directory `<template_directory>` does not exist.
>
> To create a new template, use `/infrakit:create_cloudformation_code`."
**HALT**

Check for a CloudFormation template file:

| File Pattern | Required |
|--------------|----------|
| `template.yaml` (or `template.json` / `*.template`) | ✅ Yes |

**If no template is found:**
> "⚠️ The directory does not appear to contain a valid CloudFormation template (no `template.yaml`).
>
> A) **Continue anyway** — I'll work with what I find
> B) **Use create_cloudformation_code** — Create from scratch
> C) **Cancel**"

**WAIT** for response.

---

## Phase 3: Validate and Generate Template Context Files

### 3.1 Check for Required Template Files

Check for these artifact files in `<template_directory>`:

| File | Purpose |
|------|---------|
| `.infrakit_context.md` | Template interface summary — parameters, outputs, resources |
| `.infrakit_changelog.md` | Append-only history of all changes applied to this template |
| `README.md` | User-facing usage docs (deploy example, parameters, outputs) |

**If all exist**: Read them all and proceed to Phase 4.

**If any are missing**: Scan the existing template to generate the missing ones (Phases 3.2–3.3).

> **Note**: InfraKit does not maintain a separate contract file. `template.yaml` is the machine-readable interface contract — every parameter type, output source, and resource type lives there. The README adds the human-readable usage layer on top.

### 3.2 Scan Existing Template

Read the template file(s) in `<template_directory>`. Extract:

**From `Parameters`:**
- All parameter names, types, defaults, descriptions, and `NoEcho` flags
- Which parameters are required (no default)

**From `Resources`:**
- All resources provisioned (logical ID and `Type`)
- `DeletionPolicy` / `UpdateReplacePolicy` on stateful resources
- Tag patterns applied

**From `Outputs`:**
- All output names, values (source expression), and whether they are `Export`ed

**From `Conditions` / `Mappings`:**
- Environment-gating logic and lookup tables

### 3.3 Generate Missing Files

For each file that does not exist, generate it now:

---

**`.infrakit_context.md`** (if missing):

```markdown
# InfraKit Context: <template-name>

**Purpose**: <one-line description reconstructed from the template>
**Track**: (reconstructed) | **Completed**: <YYYY-MM-DD of last modification>
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

<!-- Reconstructed by `/infrakit:update_cloudformation_code` from template analysis. -->
```

---

**`.infrakit_changelog.md`** (if missing):

```markdown
# InfraKit Changelog: <template-name>

<!-- Change history for this template. Each update track appends an entry here. -->

## (reconstructed) — <YYYY-MM-DD of last modification>

**Change Type**: (original creation — reconstructed)
**Summary**: Initial template, reconstructed from analysis.

### Resources Managed
<list of resource types from template.yaml>

<!-- Reconstructed by `/infrakit:update_cloudformation_code` from template analysis. -->
```

---

**`README.md`** (if missing):

If the template has no `README.md` yet, the IaC Engineer regenerates one from `template.yaml` during Phase 9 (Implementation). For Phase 3 (validation), absence of README.md is not blocking — it will be produced/refreshed at the end of `/infrakit:implement` anyway.

### 3.4 Present Generated Files for Review

Present only the files that were newly generated:

> "I've generated the following template files from analysis:
>
> **Generated:**
> - <list only newly generated files>
>
> **Template Summary:**
>
> | Aspect | Value |
> |--------|-------|
> | Resources | <comma-separated list of types> |
> | Required Parameters | <N> |
> | Optional Parameters | <N> |
> | Outputs | <N> |
>
> Please review the generated files. What would you like to do?
>
> A) **Accept** — Files look correct, proceed with the update
> B) **I've updated them manually** — Edit the files now, say 'done' when ready
> C) **Regenerate** — Tell me what to correct"

**WAIT** for response.

- If **A**: Proceed to Phase 4.
- If **B**: Wait for 'done', re-read all files, then proceed to Phase 4.
- If **C**: Ask what to correct, regenerate the relevant files, loop back to 3.4.

---

## Phase 4: Create Update Track

Generate a track name: `<template-name>-update-<YYYYMMDD-HHMMSS>`

Example: `s3-secure-bucket-update-20260101-120000`

Create the track directory:
```bash
mkdir -p .infrakit_tracks/tracks/<track-name>
```

Register in `.infrakit_tracks/tracks.md` — add a row with Status `🔵 initializing` and Type `update`.

---

## Phase 5: Cloud Solutions Engineer — Requirements Clarification and Spec

This phase is **interactive** — you and the user iterate on what's changing. Run it **inline** in your current context regardless of whether your harness supports subagents: a subagent can't pause to wait for user input.

Adopt the Cloud Solutions Engineer persona by reading `.infrakit/agent_personas/cloud_solutions_engineer.md` and following its behaviour for the duration of Phase 5. Later phases (Architect and Security review) can be delegated to subagents when available — see Phases 6 and 7.

> "I'll now guide you through defining the changes for this template.
> Acting as the **Cloud Solutions Engineer**, I'll ask clarifying questions until I fully understand your requirements before writing the spec."

### 5.1 Change Description

> "What changes do you want to make to this template?
>
> Examples:
> - 'Add a backup retention parameter'
> - 'Enable encryption at rest by default'
> - 'Expose the resource ARN as an output'
>
> Describe your changes:"

**WAIT** for response.

### 5.2 Change Classification

Analyze the user's description and classify:

- **Additive** — New optional parameters or resources (backward compatible; existing stacks unaffected)
- **Behavioral** — Changing defaults or logic (may affect existing stacks on next update)
- **Breaking** — Removing parameters, changing parameter types, new required parameters, or changes that force resource **replacement** (a new physical resource + deletion of the old)

> "Based on your description, these changes appear to be: **<classification>**
>
> **Impact assessment:**
> - Existing stacks: <no change / may need new parameter values / must update before next deploy>
> - Stack-update impact: <no-interruption / some-interruption / replacement>
>
> Do you agree? (yes/no/modify)"

**WAIT** for response.

### 5.3 Requirements Clarification Loop

Ask clarifying questions based on the change type, **one at a time**. **WAIT** after each question before asking the next.

Cover these areas (only ask what is not yet answered):

**For new parameters:**
- What `Type` should the parameter be? (String, Number, List, AWS-specific type)
- Is it required or optional? If optional, what is the `Default`?
- What constraints apply? (`AllowedValues`, `AllowedPattern`, `MinValue`/`MaxValue`)
- Is it sensitive (needs `NoEcho`)?
- Which resource(s) does it configure and how?

**For behavioral changes:**
- What is the old default and what should the new default be?
- Which existing stacks will be affected on next update?
- Will the change be no-interruption, some-interruption, or replacement?

**For new outputs:**
- What is the source expression? (`!GetAtt` / `!Ref`)
- Should it be `Export`ed for cross-stack use?

**For resource changes:**
- Will any change force replacement of a stateful resource? (data-loss risk)
- Are new resources being added alongside existing ones?

**For security requirements:**
- Encryption at rest or in transit?
- IAM policy or role constraints?
- Security group / network ACL implications?

After each answer, assess: **Are all requirements for this change fully clear?**

When requirements are complete, summarize and confirm:

> "I've gathered all the requirements. Here's my understanding:
>
> <bulleted summary of every change and the reasoning behind it>
>
> Is this correct and complete? (yes / add more)"

**WAIT** for response. If the user adds more, continue the clarification loop. Repeat until the user confirms.

### 5.4 Generate spec.md

Write to `.infrakit_tracks/tracks/<track-name>/spec.md`:

```markdown
# Update Specification: <Template Name>

## Change Overview

| Property | Value |
|----------|-------|
| **Change Type** | <Additive/Behavioral/Breaking/Mixed> |
| **Migration Required** | <Yes/No> |
| **Stack-Update Impact** | <No-interruption/Some-interruption/Replacement> |

## Existing Template (Current State)

**Parameters (Current):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ... | ... | ... | ... |

## Proposed Changes

### ADD: New Elements

| Element | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `<param>` | `<type>` | <yes/no> | <default> | ... |

### MODIFY: Changed Elements

| Element | Current | New | Impact |
|---------|---------|-----|--------|
| `<param>` | `<old>` | `<new>` | <Breaking/Non-breaking> |

### REMOVE: Deprecated Elements

| Element | Reason | Migration Path |
|---------|--------|----------------|
| `<param>` | `<reason>` | `<alternative>` |

## Security Requirements
- <requirement>

## Acceptance Criteria
- [ ] All ADD changes implemented
- [ ] All MODIFY changes implemented
- [ ] All REMOVE changes handled safely
- [ ] Migration guide created (if breaking)
```

### 5.5 Generate migration.md (If Breaking Changes)

If changes are classified as Breaking or Mixed, also write `.infrakit_tracks/tracks/<track-name>/migration.md`:

```markdown
# Migration Guide: <Template Name>

## Overview

| Property | Value |
|----------|-------|
| **Change Type** | Breaking |
| **Breaking Changes** | `<count>` |

## Breaking Changes

### 1. <Change Description>

**What changed:**
- Old: `<old behavior/parameter/resource>`
- New: `<new behavior/parameter/resource>`

**Migration Steps:**
1. <Step 1>
2. <Step 2>

**Stack-update impact:**
- Review the change set: `aws cloudformation create-change-set ...` — confirm whether stateful resources show `Replacement: True`.
- If a resource will be replaced: document whether to snapshot/back up data first, or import the existing physical resource with a `resource import` operation.
- Note any `Export` name changes that would break dependent stacks (you cannot delete an exported output that another stack imports).

## Pre-Migration Checklist
- [ ] Back up data on any resource that may be replaced
- [ ] Generate and review a change set before executing
- [ ] Confirm no dependent stack imports an output being removed/renamed
- [ ] Test the update in a non-production stack first

## Rollback Plan
1. <Rollback step 1>
2. <Rollback step 2>
```

### 5.6 Spec Options Loop

> "I've generated the update specification.
>
> **Files:**
> - `.infrakit_tracks/tracks/<track-name>/spec.md`
> <if breaking> - `.infrakit_tracks/tracks/<track-name>/migration.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change
> B) **Manual Changes** — Edit the file, say 'done' when ready
> C) **Proceed** — Hand off to Cloud Architect for design options"

**WAIT** for response. Loop until user chooses C.

---

## Phase 6: Cloud Architect — Design Options (delegated when subagents are available)

The **analysis** part of this phase is read-only and benefits from subagent isolation; the **option-selection** part needs user input and must stay inline.

**On Claude Code (`Task` tool with custom subagent type):**

Invoke the `Task` tool with:

- `subagent_type`: `cloud-architect` (registered at `.claude/agents/cloud-architect.md`)
- `description`: `"Cloud Architect design options for <track-name>"`
- `prompt`: `"For the update spec at .infrakit_tracks/tracks/<track-name>/spec.md, identify backward-compatibility constraints and stack-update impact (especially any resource replacement) by reading the existing template.yaml and .infrakit_context.md in the template directory. Then produce 2–3 distinct, named architecture options (Option A/B/C) following the format in Phase 6.2 of /infrakit:update_cloudformation_code. Do NOT pick one; return all options for the user to choose from. Do not modify any files."`

Paste the returned options into your reply and proceed to Phase 6.2 (user selection).

**On Codex / Gemini / Copilot / generic (no custom-subagent primitive):**

Read `.infrakit/agent_personas/cloud_architect.md` and adopt that persona inline. Mark the boundary in your reply ("entering Cloud Architect phase"). Run the analysis described in Phase 6.1 and produce the option set described in Phase 6.2.

> "Handing off to the Cloud Architect..."
> "As the **Cloud Architect**, I'll review the spec and present distinct architecture options for implementing these changes. You choose the direction."

### 6.1 Architecture Analysis

Review the spec alongside `.infrakit_context.md` and `template.yaml` (the existing template — your machine-readable contract). Identify:
- Backward compatibility constraints from the current parameters/outputs
- Stack-update impact of each possible approach (no-interruption / some-interruption / replacement)
- Whether any `Export`ed output is consumed by dependent stacks
- Cost, reliability, and complexity trade-offs of each approach

### 6.2 Present Architecture Options

Present **2–3 distinct, named architecture options**. Each must include a trade-off table so the user can make an informed choice.

> "I've analysed the spec and identified the following design options:
>
> ---
>
> ### Option A: <Short Name> (e.g., Minimal / In-place)
>
> **Approach**: <1–2 sentence description of the design>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | Stack-Update Impact | <No-interruption / Some-interruption / Replacement> |
> | Replaces Stateful Resource | <Yes / No> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> ### Option B: <Short Name> (e.g., Recommended)
>
> **Approach**: <1–2 sentence description>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | Stack-Update Impact | <No-interruption / Some-interruption / Replacement> |
> | Replaces Stateful Resource | <Yes / No> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> ### Option C: <Short Name> (e.g., Forward-Looking)
>
> **Approach**: <1–2 sentence description>
>
> | Aspect | Assessment |
> |--------|-----------|
> | Backward Compatibility | <Full / Partial / Breaking> |
> | Stack-Update Impact | <No-interruption / Some-interruption / Replacement> |
> | Replaces Stateful Resource | <Yes / No> |
> | Implementation Complexity | <Low / Medium / High> |
> | Migration Required | <Yes / No> |
>
> **Trade-offs:**
> - ✅ <primary advantage>
> - ⚠️ <key limitation or risk>
>
> ---
>
> Which option would you like to proceed with? (A / B / C / Discuss an option)"

**WAIT** for response. If user wants to discuss an option, explain it further and loop. Continue until the user makes a final selection.

### 6.3 Apply Selected Option

Update `.infrakit_tracks/tracks/<track-name>/spec.md` — append an **Architecture Decision** section:

```markdown
## Architecture Decision

**Selected Option**: <Option A/B/C> — <Short Name>
**Rationale**: <why this option was selected>

### Implementation Approach
<detailed description of the chosen design>

### Stack-Update Impact Details
- Update behaviour: <no-interruption / some-interruption / replacement>
- Resources replaced: <none / list — and data-protection steps>
- Export changes: <none / list — and dependent-stack impact>

### Backward Compatibility Notes
<what existing stacks will experience during and after the update>
```

> "✅ Architecture option recorded in spec.
>
> Handing off to security review..."

---

## Phase 7: Cloud Security Engineer Review

**Announce:**
> "Reviewing the update specification as the **Cloud Security Engineer**."

**Resolve compliance frameworks from `.infrakit/context.md` first.** Look for a `## Compliance` (or `## Security & Compliance` → `### Compliance Frameworks`) section listing frameworks (SOC 2, ISO 27001, HIPAA, PCI-DSS, NIST 800-53, FedRAMP, CIS Benchmarks).

- If context.md declares frameworks, announce: `"Using compliance frameworks declared in .infrakit/context.md: <frameworks>"` and use that list.
- If context.md is silent on compliance, only then ask the user which frameworks apply. **WAIT** for response.

**On Claude Code (`Task` tool with custom subagent type):**

Invoke the `Task` tool with:

- `subagent_type`: `cloud-security-engineer` (registered at `.claude/agents/cloud-security-engineer.md`)
- `description`: `"Cloud Security Engineer audit of update <track-name>"`
- `prompt`: `"Audit the updated spec at .infrakit_tracks/tracks/<track-name>/spec.md (including its Architecture Decision section) against these frameworks: {frameworks chosen above}. Return the structured findings report per your persona. Do not modify any files."`

Paste the report into your reply and proceed to the feedback loop below.

**On Codex / Gemini / Copilot / generic (no custom-subagent primitive):**

Read `.infrakit/agent_personas/cloud_security_engineer.md` and adopt that persona inline. Mark the boundary in your reply ("entering Cloud Security Engineer phase"). Audit the selected architecture option against the chosen frameworks and produce the same report format.

**DO NOT modify `spec.md` automatically. Present findings first.**

> "**Security Review Complete**
>
> | Framework | Status | Findings |
> |-----------|--------|----------|
> | <framework> | <COMPLIANT / GAPS FOUND> | <N> findings |
>
> A) **Apply all fixes** — Update spec.md with all remediations
> B) **Apply selected fixes** — Tell me which findings to address
> C) **Waive a finding** — Document with justification
> D) **Discuss** — Explain a finding in detail
> E) **Accept as-is** — Proceed without changes"

**WAIT** for response. Loop until user is satisfied and makes a final choice.

---

## Phase 8: Final Spec Confirmation

Present a combined summary of both reviews:

> "**Update Review Summary**
>
> | Review | Verdict | Outcome |
> |--------|---------|---------|
> | Architecture | <Selected Option Name> | Applied to spec |
> | Security | <COMPLIANT / COMPLIANT_WITH_WAIVERS / ACCEPTED> | <N> findings resolved |
>
> **Final Spec**: `.infrakit_tracks/tracks/<track-name>/spec.md`
>
> A) **Confirm** — Spec is finalized, register the track
> B) **Make changes** — Edit spec now, say 'done' when ready
> C) **Re-run a review** — Return to architect or security review"

**WAIT** for response. Loop until user confirms.

---

## Phase 9: Register Track

Update `.infrakit_tracks/tracks.md` — change the track's Status to `📝 spec-generated`.

> "✅ **Update spec finalized for `<template-name>`!**
>
> **Track**: `<track-name>`
> **Change Type**: `<Additive/Behavioral/Breaking>`
> **Architecture**: `<Selected Option Name>`
>
> **Files created:**
> - `.infrakit_tracks/tracks/<track-name>/spec.md`
> <if breaking> - `.infrakit_tracks/tracks/<track-name>/migration.md`
>
> **Next step**: Run `/infrakit:plan <track-name>` to generate the implementation plan."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| Directory not found | Halt, suggest `/infrakit:create_cloudformation_code` |
| Template missing | Warn, offer options |
| Template parse errors | Report file and error, halt |
| Breaking change without migration | Generate migration.md automatically |
| Context files unreadable | Report error, regenerate from template |
