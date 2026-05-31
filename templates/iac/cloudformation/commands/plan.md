---
description: "Generate a CloudFormation implementation plan (plan.md) and task list (tasks.md) for a track from its spec."
argument-hint: "<track-name>"
handoffs:
  - label: "Analyze Consistency"
    agent: "infrakit:analyze"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the track name from `$ARGUMENTS`. If not provided, ask:

> "Which track would you like to generate a plan for?
> Example: `s3-secure-bucket-20260101-120000`"

**WAIT** for response before continuing.

---

## System Directive

You are the **CloudFormation Engineer** generating a detailed implementation plan for an infrastructure track. The plan translates the approved spec into a concrete CloudFormation template blueprint.

**You are generating plan.md — you are NOT writing the template yet.**

Read `.infrakit/agent_personas/cloudformation_engineer.md` for detailed persona behavior (if present).

---

## Step 1: Setup Check

Verify required files exist:

| File | Path | Required |
|------|------|----------|
| Project Context | `.infrakit/context.md` | ✅ Yes |
| Coding Style | `.infrakit/coding-style.md` | ✅ Yes |
| Tagging | `.infrakit/tagging-standard.md` | ✅ Yes |
| Spec | `.infrakit_tracks/tracks/<track-name>/spec.md` | ✅ Yes |

**If context.md, coding-style.md, or tagging-standard.md is missing:**
> "❌ Project not fully initialized. Run `/infrakit:setup` first."
**HALT**

**If spec.md is missing:**
> "❌ `spec.md` not found. Run `/infrakit:create_cloudformation_code <track-name>` to create the spec."
**HALT**

---

## Step 2: Load Standards and Spec

Read the following files:

1. `.infrakit/context.md` — AWS account structure, regions, naming conventions
2. `.infrakit/coding-style.md` — Mandatory coding standards (section order, tagging, secrets, intrinsic functions)
3. `.infrakit/tagging-standard.md` — Required tags for all resources
4. `.infrakit_tracks/tracks/<track-name>/spec.md` — Requirements, parameters, outputs, security

---

## Step 3: Research Resource Types and Properties

**CRITICAL**: Never guess resource type strings or property names.

For each resource required by the spec:

1. Identify the correct CloudFormation resource type (e.g. `AWS::RDS::DBInstance`, `AWS::S3::Bucket`)
2. Look up the type and its properties using:
   ```text
   search_web("site:docs.aws.amazon.com/AWSCloudFormation aws-resource-<service>-<type>")
   ```
   Example: `search_web("site:docs.aws.amazon.com/AWSCloudFormation aws-resource-rds-dbinstance")`
3. Verify the required and optional properties, their value types, and the `Fn::GetAtt` return attributes (for Outputs)
4. Confirm whether the type supports a `Tags` property
5. Record the verified details in the plan

Prefer the `aws-documentation` MCP (`search_documentation`, `read_documentation`) when installed; fall back to `WebSearch`.

---

## Step 4: Design Parameter Mapping

Map each spec parameter to a CloudFormation `Parameters` entry:

| Spec Parameter | Parameter Name | Type | Default | Constraints (AllowedValues / Pattern) |
|----------------|----------------|------|---------|----------------------------------------|
| `<param>` | `<PascalCase>` | `<CFN type>` | `<default>` | `<constraint if any>` |

Map each parameter to the resource property it controls:

| Parameter | Resource (Logical ID) | Property Path |
|-----------|-----------------------|---------------|
| `!Ref <Name>` | `<LogicalId>` | `<Property>` |

Flag any parameter that must be `NoEcho: true` (secrets).

---

## Step 5: Design Output Mapping

Map each spec output to its source:

| Spec Output | Output Name | Value | Exported? |
|-------------|-------------|-------|-----------|
| `<output>` | `<PascalCase>` | `!GetAtt <LogicalId>.<Attribute>` | yes/no |

---

## Step 6: Design Tagging Strategy

Based on `.infrakit/tagging-standard.md`, define the tagging approach:

| Tag Key | Value Source | Notes |
|---------|-------------|-------|
| `managed-by` | `cloudformation` | Static — all taggable resources |
| `environment` | `!Ref Environment` | From parameter |
| `<project-tag>` | `!Ref <Param>` / static | From caller / project |

Note any resource types in the plan that do **not** support `Tags` (so the implementer doesn't invent the property).

---

## Step 7: Write plan.md

Write to `.infrakit_tracks/tracks/<track-name>/plan.md`:

```markdown
# Implementation Plan: <Template Name>

## Summary
<Brief description of what will be built>

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `<track-name>` |
| **Cloud Provider** | AWS |
| **Template Directory** | `<template-directory>` |
| **Template Format** | YAML (`2010-09-09`) |

## File Structure

```
<template-directory>/
├── template.yaml       # Parameters, Resources, Outputs
├── parameters/
│   ├── dev.json        # Example parameter overrides (dev)
│   └── prod.json       # Example parameter overrides (prod)
└── README.md           # Usage documentation
```text

## Parameters Design

| Parameter | Type | Default | NoEcho | Constraints | Description |
|-----------|------|---------|--------|-------------|-------------|
| `<name>` | `<type>` | `<default>` | yes/no | `<constraint>` | `<desc>` |

## Conditions

| Condition | Expression | Purpose |
|-----------|------------|---------|
| `<Name>` | `!Equals [...]` | `<env-gated behaviour>` |

## Resources to Provision

| # | Logical ID | Type | Key Properties | DeletionPolicy | Purpose |
|---|------------|------|----------------|----------------|---------|
| 1 | `<LogicalId>` | `<AWS::Service::Type>` | `<key props>` | `<Retain/Snapshot/Delete>` | `<purpose>` |

## Outputs Design

| Output | Value | Exported | Description |
|--------|-------|----------|-------------|
| `<name>` | `!GetAtt <LogicalId>.<attr>` | yes/no | `<desc>` |

## Tagging Strategy

<Describe tagging approach — required tags, parameter/pseudo-param sources, any types lacking Tags support>

## Implementation Phases

1. **Header** — `AWSTemplateFormatVersion` + `Description`
2. **Parameters** — declare all parameters with types, defaults, constraints, NoEcho
3. **Conditions / Mappings** — environment gating and lookups
4. **Resources** — define all resources with verified properties, tags, deletion policies
5. **Outputs** — declare outputs (and exports where needed)
6. **parameters/*.json + README.md** — example deploys and documentation

## Constraints from coding-style.md

- <Key constraint 1 from project coding style>
- <Key constraint 2>
- **Never** hardcode secrets — use `NoEcho` parameters + dynamic references
- **Never** default open ingress / public access without a Parameter + Condition
- **Always** enable encryption at rest for storage resources
- **Always** set DeletionPolicy/UpdateReplacePolicy on stateful resources

## Notes

### Known Challenges
- <any implementation challenges identified>

### Design Decisions
- <key decisions made during planning>
```

---

## Step 8: Feedback Loop

After writing plan.md:

> "I've generated the implementation plan.
>
> **File**: `.infrakit_tracks/tracks/<track-name>/plan.md`
>
> What would you like to do?
>
> A) **Regenerate** — Tell me what to change and I'll revise
> B) **Manual Changes** — Edit the file, say 'done' when ready
> C) **Proceed** — Generate task list and mark track ready"

**WAIT** for response. Loop until user chooses C.

---

## Step 9: Auto-Generate tasks.md

After the user accepts the plan, expand the Implementation Phases from plan.md into granular checkbox tasks.

Write to `.infrakit_tracks/tracks/<track-name>/tasks.md`:

```markdown
# Implementation Tasks: <Template Name>

**Track**: `<track-name>`
**Generated**: <YYYY-MM-DD>
**Source Plan**: `.infrakit_tracks/tracks/<track-name>/plan.md`

## Phase 1: Header
- [ ] T1.1: Write `AWSTemplateFormatVersion: "2010-09-09"` and a one-line `Description`

## Phase 2: Parameters
<one task per parameter from the Parameters Design table in plan.md:>
- [ ] T2.1: Declare parameter `<Name>` (type: `<type>`, default: `<default>`, NoEcho: <yes/no>)
- [ ] T2.N: ...

## Phase 3: Conditions / Mappings
<one task per condition/mapping from plan.md, or "none">
- [ ] T3.1: Declare condition `<Name>`

## Phase 4: Resources
<one task per resource from the Resources to Provision table in plan.md:>
- [ ] T4.1: Write resource `<LogicalId>` (`<Type>`) with verified properties + Tags + DeletionPolicy
- [ ] T4.N: ...

## Phase 5: Outputs
<one task per output from the Outputs Design table in plan.md:>
- [ ] T5.1: Declare output `<Name>` sourced from `!GetAtt <LogicalId>.<attr>` (Export: <yes/no>)
- [ ] T5.N: ...

## Phase 6: Examples & Docs
- [ ] T6.1: Write `parameters/dev.json` and `parameters/prod.json` example overrides
- [ ] T6.2: Document all parameters in a table (name, type, default, description)
- [ ] T6.3: Document all outputs in a table (name, description, exported)
- [ ] T6.4: Add a deploy example (`aws cloudformation deploy ...`)

## Phase 7: Validate
- [ ] T7.1: Run `cfn-lint template.yaml`
- [ ] T7.2: Run `aws cloudformation validate-template` (if credentials available)
```

**Expand dynamically**: use the actual parameter names, logical IDs, resource types, and output names from plan.md — do not use placeholders where real values are known.

> "✅ tasks.md generated."

---

## Step 10: Update Track Status

Update `.infrakit_tracks/tracks.md` — change the track's Status to `📋 planned`.

> "✅ **Plan and task list ready for `<track-name>`!**
>
> **Files:**
> - `.infrakit_tracks/tracks/<track-name>/plan.md`
> - `.infrakit_tracks/tracks/<track-name>/tasks.md`
>
> **Next step**: Run `/infrakit:implement <track-name>` to start implementation."

---

## Error Handling

| Error | Action |
|-------|--------|
| Setup files missing | Halt, direct to `/infrakit:setup` |
| spec.md missing | Halt, direct to `/infrakit:create_cloudformation_code` |
| Resource type/property unknown | Use `search_web("site:docs.aws.amazon.com/AWSCloudFormation ...")` to look it up |
| plan.md already exists | Ask: overwrite or update? |
