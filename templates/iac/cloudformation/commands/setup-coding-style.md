---
description: "Configure the CloudFormation coding style for this project by filling in the project-specific values in .infrakit/coding-style.md."
argument-hint: "[optional: describe any specific conventions to apply]"
handoffs:
  - label: "Create CloudFormation Code"
    agent: "infrakit:create_cloudformation_code"
  - label: "Check Status"
    agent: "infrakit:status"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## System Directive

You are configuring the CloudFormation coding style guide for this project. Your task is to gather project-specific conventions and fill in all `[PLACEHOLDER]` values in `.infrakit/coding-style.md`.

**CRITICAL**: Read `.infrakit/coding-style.md` before asking any questions. If placeholders are already filled in, present the current values and offer to update specific sections rather than regenerating from scratch.

---

## Phase 1: Prerequisites

### 1.1 Load Project Context

Read `.infrakit/context.md` and extract the following values (they will be used to fill placeholders without re-asking the user):

| Value | Source |
|-------|--------|
| `<project_name>` | **Project Name** row in Project Information table |
| `<environments>` | **Environments** row in Project Information table |
| `<naming_conventions>` | Naming Conventions table |

If `.infrakit/context.md` is missing, stop and tell the user:

> "`.infrakit/context.md` is required before configuring coding style.
> Please run `/infrakit:setup` first."

### 1.2 Check Existing Coding Style File

Read `.infrakit/coding-style.md`.

- **File has `[PLACEHOLDER]` values remaining**: Proceed to Phase 2 to gather information and fill them in.
- **File is fully populated**: Present a summary of current values and ask:
  > "Your `.infrakit/coding-style.md` is already configured. Would you like to update any section?
  >
  > A) **Update specific section** — Tell me which one
  > B) **Review all values** — Walk through each setting
  > C) **No changes needed** — Exit"
  **WAIT** for response before continuing.
- **File missing**: Tell the user:
  > "`.infrakit/coding-style.md` not found. Please run `infrakit init` to initialize the project first."
  **STOP.**

---

## Phase 2: Gather Coding Style Information

Ask these questions **one at a time**. Wait for each response before asking the next.

**Question 1: Template Format & Tooling**
> "What template format and deployment tooling does this project use?
>
> Examples:
> - 'YAML templates; `aws cloudformation deploy` from GitHub Actions; change sets reviewed before prod'
> - 'YAML; AWS SAM CLI for build + deploy'
> - 'JSON templates; deployed via a custom pipeline'
>
> Specify your template format (YAML/JSON) and how stacks are deployed (or press Enter for YAML + `aws cloudformation deploy`):"

**WAIT** for response. *(Fills: `[TEMPLATE_FORMAT]`, `[DEPLOYMENT_TOOLING]`)*

**Question 2: Linting Policy**
> "What is your linting / static-analysis policy for templates?
>
> Examples:
> - 'cfn-lint pinned in CI; fail the build on E and W rules'
> - 'cfn-lint + cfn-guard for policy-as-code; Checkov for security scanning'
>
> Describe your linter setup (or press Enter for `cfn-lint, fail on errors`):"

**WAIT** for response. *(Fills: `[CFN_LINT_POLICY]`)*

**Question 3: Template Directory Structure**
> "What is your template directory structure?
>
> Default structure:
> ```text
> templates/
>   <resource>/
>     template.yaml
>     parameters/
>       dev.json
>       prod.json
>     README.md
> ```
>
> Describe any deviations (or press Enter to use the default):"

**WAIT** for response. *(Fills: `[PROJECT_FILE_STRUCTURE]`)*

**Question 4: Project Prefix & Stack Naming**
> "What prefix and naming pattern should stacks and exported outputs use?
>
> Examples:
> - Prefix `acme` with pattern `{prefix}-{resource}-{env}` → `acme-rds-prod`
> - Prefix `myapp` with pattern `{prefix}-{name}-{env}` → `myapp-vpc-staging`
>
> Specify your project prefix (or press Enter to derive from the project name):"

**WAIT** for response. *(Fills: `[PROJECT_PREFIX]`)*

**Question 5: Tagging Strategy**
> "How should required tags be applied across resources?
>
> Examples:
> - 'Per-resource `Tags` lists in the template, plus stack-level `--tags` on `aws cloudformation deploy` for org-wide tags'
> - 'Per-resource Tags only'
>
> Choose your strategy (or press Enter to use per-resource Tags + stack-level `--tags`):"

**WAIT** for response. *(Fills: `[DEFAULT_TAGS_STRATEGY]`)*

**Question 6: Project-Specific Tags**
> "What tags should all taggable resources carry, beyond the baseline (`managed-by`, `environment`, `project`)?
>
> Examples:
> - `cost-center` — from `!Ref CostCenter`
> - `team` — from `!Ref Team`
>
> List your tags and their value sources as `key — source` pairs (or press Enter to use the baseline only):"

**WAIT** for response. *(Fills: `[PROJECT_SPECIFIC_TAGS]`)*

**Question 7: Deployment & Change Management**
> "What is your change-management approach for stack updates?
>
> Examples:
> - 'All prod changes via `create-change-set` + review before execute; stack policies protect stateful resources; weekly drift detection'
> - 'Direct `deploy` in dev; change sets required in prod'
>
> Describe your approach (or press Enter to require reviewed change sets for prod):"

**WAIT** for response. *(Fills: `[STACK_POLICY_APPROACH]`)*

**Question 8: Security Defaults**
> "What are your project-specific security defaults for CloudFormation resources?
>
> Examples:
> - `StorageEncrypted: true` on all RDS regardless of environment
> - `PubliclyAccessible` defaults false; override requires a Parameter + Condition and security sign-off in spec.md
> - `DeletionPolicy: Snapshot` for prod databases; `Delete` for dev/staging
> - S3 `PublicAccessBlockConfiguration` all four flags true
>
> Describe your security defaults (or press Enter to inherit from context.md security standards):"

**WAIT** for response. *(Fills: `[PROJECT_SECURITY_DEFAULTS]`)*

---

## Phase 3: Fill Placeholders in .infrakit/coding-style.md

Read `.infrakit/coding-style.md` and replace every `[PLACEHOLDER]` using the values gathered in Phase 2 and loaded from `.infrakit/context.md`:

| Placeholder | Source |
|-------------|--------|
| `[PROJECT_NAME]` | `<project_name>` from context.md |
| `[TEMPLATE_FORMAT]` | Q1 — YAML or JSON |
| `[DEPLOYMENT_TOOLING]` | Q1 — how stacks are deployed |
| `[CFN_LINT_POLICY]` | Q2 |
| `[PROJECT_FILE_STRUCTURE]` | Q3 (or default structure) |
| `[PROJECT_PREFIX]` | Q4 |
| `[DEFAULT_TAGS_STRATEGY]` | Q5 |
| `[PROJECT_SPECIFIC_TAGS]` | Q6 — formatted as markdown table rows |
| `[STACK_POLICY_APPROACH]` | Q7 |
| `[PROJECT_SECURITY_DEFAULTS]` | Q8 |

Keep all non-placeholder content intact — the non-negotiable rules, code examples, and reference patterns must not be modified.

**Present to user:**
> "I've updated `.infrakit/coding-style.md`. Please review:
>
> A) **Accept** — Looks good
> B) **Edit** — Make changes, say 'done' when ready
> C) **Regenerate** — Tell me what to change"

**WAIT** for response. **Loop until user accepts.**

---

## Phase 4: Completion

> "✅ **CloudFormation coding style configured!**
>
> **File updated:**
> - `.infrakit/coding-style.md` — CloudFormation coding standards ✅
>
> **Next Steps:**
> - Run `/infrakit:create_cloudformation_code` to create your first template
> - Run `/infrakit:status` to see all track statuses"

---

## Error Handling

| Error | Action |
|-------|--------|
| `.infrakit/context.md` missing | Stop — direct user to run `/infrakit:setup` first |
| `.infrakit/coding-style.md` missing | Stop — direct user to run `infrakit init` to initialize the project |
| User skips a question | Leave the corresponding `[PLACEHOLDER]` as-is and note it in the completion summary |
| User provides partial information | Use sensible defaults for derivable values; mark the rest as TODOs |
