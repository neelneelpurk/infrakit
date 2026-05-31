# [PROJECT_NAME] CloudFormation Coding Style Guide
<!-- Example: Acme Platform CloudFormation Coding Style Guide -->

> This document captures both universal CloudFormation standards (non-negotiable)
> and project-specific conventions for this platform. Run
> `/infrakit:setup-coding-style` to populate the placeholder sections.

All CloudFormation engineers **MUST** follow these standards when generating
infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Template Format** | [TEMPLATE_FORMAT] |
| **Template Format Version** | `2010-09-09` (only valid value) |
| **Tooling** | [DEPLOYMENT_TOOLING] |
| **Linter** | [CFN_LINT_POLICY] |

<!-- Example:
| Template Format | YAML |
| Tooling | aws cloudformation deploy via GitHub Actions; change sets reviewed before prod |
| Linter | cfn-lint pinned in CI; fail on W and E rules |
-->

---

## 2. File Organization

**Template directory structure:**

```text
[PROJECT_FILE_STRUCTURE]
```

<!-- Example:
templates/
  s3-secure-bucket/
    template.yaml
    parameters/
      dev.json
      prod.json
    README.md
  rds-postgres/
    template.yaml
    parameters/
      dev.json
      prod.json
    README.md
-->

**Non-negotiable rules (apply to all projects):**

- **One template per directory**: each reusable unit gets its own
  `template.yaml`.
- **YAML over JSON** unless a tool requires JSON — YAML allows comments and is
  far more readable. Use `2010-09-09` as the format version.
- **Example parameters live in `parameters/`**: one file per environment, used
  with `--parameter-overrides` / `--parameters`.
- **`README.md` per template**: usage, parameters, outputs, validation commands.

---

## 3. Naming Conventions

### Template elements

| Element | Pattern | Example |
|---------|---------|---------|
| Logical ID (resource) | `PascalCase`, descriptive | `PrimaryDatabase`, `LogsBucket` |
| Parameter name | `PascalCase` | `InstanceClass`, `Environment` |
| Output name | `PascalCase` | `DatabaseEndpoint` |
| Mapping / Condition name | `PascalCase` | `RegionMap`, `IsProd` |

### Stack & physical naming

**Project prefix**: `[PROJECT_PREFIX]`
<!-- Example: acme — used to namespace stack names and exported output names -->

| Resource Category | Naming Pattern | Example |
|-------------------|----------------|---------|
| Stack name | `[PREFIX]-[resource]-[env]` | `[PROJECT_PREFIX]-rds-prod` |
| Exported output | `${AWS::StackName}-[name]` | `acme-rds-prod-Endpoint` |

**Non-negotiable rules:**

- **PascalCase** for all template logical IDs, parameters, and outputs.
- **Never hardcode physical resource names** that must be globally unique (S3
  bucket names, etc.) — derive them with `!Sub` from `AWS::StackName` /
  parameters, or omit the name and let CloudFormation generate it.
- Export names are global per region/account — namespace them with
  `!Sub "${AWS::StackName}-..."` to avoid collisions.

---

## 4. Template Structure (MANDATORY STANDARDS)

### Section order

Author sections in this canonical order:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: <required, one line>
Metadata:        # optional — parameter groups / interface
Parameters:
Mappings:        # optional
Conditions:      # optional
Resources:       # required
Outputs:
```

### Intrinsic functions

- Prefer the **short form** in YAML (`!Ref`, `!GetAtt`, `!Sub`, `!If`) for
  readability; never mix short and long form within the same node.
- Use `!Sub` over `!Join` for string interpolation.
- Use pseudo parameters (`AWS::Region`, `AWS::AccountId`, `AWS::Partition`,
  `AWS::StackName`) instead of hardcoded values.
- Gate environment-specific behaviour with `Conditions`, not duplicated
  templates.

### Formatting & Syntax

- **Indentation**: 2 spaces.
- **Resource ordering**: group logically (network → security → data → compute),
  dependencies before dependents where it aids readability (`DependsOn` only when
  CloudFormation can't infer the order).

---

## 5. Parameters

### Required fields

Every parameter **MUST** have:

```yaml
Parameters:
  InstanceClass:
    Type: String
    Description: <what this controls and valid values>
    Default: db.t3.micro   # omit if the parameter is required
    AllowedValues: [db.t3.micro, db.t3.small]
```

**Non-negotiable rules:**

- `Description` is **MANDATORY** for all parameters.
- Use the most specific `Type` available (`Number`, `AWS::EC2::VPC::Id`,
  `List<...>`, `AWS::SSM::Parameter::Value<...>`) — not `String` for everything.
- Constrain inputs with `AllowedValues`, `AllowedPattern`, `MinValue`/`MaxValue`,
  `MinLength`/`MaxLength` wherever the spec implies a constraint.
- Sensitive parameters (passwords, tokens) **MUST** set `NoEcho: true`, and
  **MUST NOT** have a plaintext `Default`.

---

## 6. Resource Tagging

**ALWAYS add a `Tags` property to resources whose type supports it.**

### Required Tags (MANDATORY for all taggable resources)

| Tag Key | Value | Description |
|---------|-------|-------------|
| `managed-by` | `cloudformation` | Indicates resource is managed by CloudFormation |
| `environment` | `!Ref Environment` | Deployment environment |
| `<project-tag>` | `[PROJECT_NAME]` | Project identifier |

### Tagging strategy

**Project standard**: `[DEFAULT_TAGS_STRATEGY]`
<!-- Example: per-resource Tags lists for in-template tags, plus stack-level
`--tags` on `aws cloudformation deploy` for org-wide tags propagated to all
resources that support tagging. -->

> **Note**: CloudFormation has no provider-level default-tags block. Org-wide
> tags can be applied at the **stack** level (`aws cloudformation deploy --tags`)
> and propagate to taggable resources; per-resource `Tags` cover the rest. Some
> resource types do **not** support `Tags` — do not invent the property; note
> the exception in the README instead.

### Project-Specific Tags

| Tag Key | Value Source | Description |
|---------|-------------|-------------|
[PROJECT_SPECIFIC_TAGS]

<!-- Example:
| `cost-center` | !Ref CostCenter | Billing allocation code |
| `team` | !Ref Team | Owning team name |
-->

---

## 7. Security Standards

### Non-Negotiable Rules

- **Secrets**: NEVER hardcode secrets, passwords, or API keys in a template.
- **Secrets**: mark sensitive parameters `NoEcho: true`.
- **Secrets**: resolve secret values at deploy time with dynamic references —
  `'{{resolve:secretsmanager:MySecret:SecretString:password}}'` or
  `'{{resolve:ssm-secure:/path/to/param}}'` — never literal strings.
- **Public access**: NEVER default open ingress (`0.0.0.0/0`), public S3 ACLs, or
  `PubliclyAccessible: true`. Default to closed; gate any exposure behind a
  `Parameter` + `Condition`.
- **Encryption**: ALWAYS enable encryption at rest for storage resources
  (`StorageEncrypted`, `BucketEncryption`, `KmsKeyId`, …) in staging and prod.
- **Deletion safety**: set `DeletionPolicy` (and `UpdateReplacePolicy`) to
  `Retain` or `Snapshot` on stateful resources in prod.

### Project-Specific Security Defaults

[PROJECT_SECURITY_DEFAULTS]
<!-- Example:
- StorageEncrypted: true on all RDS regardless of environment
- PubliclyAccessible defaults false; override requires a Parameter + Condition and security sign-off in spec.md
- DeletionPolicy: Snapshot for prod databases; Delete acceptable in dev
- S3 PublicAccessBlockConfiguration all four flags true
-->

---

## 8. Outputs & Exports

Every output **MUST** have a `Description`:

```yaml
Outputs:
  DatabaseEndpoint:
    Description: The connection endpoint of the RDS instance
    Value: !GetAtt PrimaryDatabase.Endpoint.Address
    Export:
      Name: !Sub "${AWS::StackName}-DatabaseEndpoint"
```

**Non-negotiable rules:**

- `Description` is **MANDATORY** for all outputs.
- Output specific attributes (`!GetAtt X.Endpoint.Address`), not whole objects.
- **Only `Export`** an output when another stack consumes it cross-stack; namespace
  the export name with `!Sub "${AWS::StackName}-..."`. Avoid exporting values that
  would lock the producing stack against updates unnecessarily.
- Never output a secret value in plaintext.

---

## 9. Deployment & Change Management

**Project standard**: `[STACK_POLICY_APPROACH]`
<!-- Example: All prod changes go through `aws cloudformation create-change-set`
+ review before execute; stack policies protect stateful resources from
replacement; drift detection runs weekly. -->

**Non-negotiable rules:**

- **NEVER** deploy template changes to prod without a reviewed change set.
- Protect stateful resources from accidental replacement (stack policies +
  `UpdateReplacePolicy`).
- Treat a change set that shows `Replacement: True` on a stateful resource as a
  breaking change — document migration steps.

---

## 10. Reference Example

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Encrypted RDS PostgreSQL instance, private by default.

Parameters:
  Environment:
    Type: String
    Description: Deployment environment
    AllowedValues: [dev, staging, prod]
  InstanceClass:
    Type: String
    Description: RDS instance class
    Default: db.t3.micro
  DBPassword:
    Type: String
    Description: Master password (prefer a dynamic reference over a literal)
    NoEcho: true

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Resources:
  PrimaryDatabase:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      Engine: postgres
      DBInstanceClass: !Ref InstanceClass
      AllocatedStorage: "20"
      StorageEncrypted: true
      PubliclyAccessible: false
      MultiAZ: !If [IsProd, true, false]
      MasterUsername: dbadmin
      MasterUserPassword: !Ref DBPassword
      Tags:
        - Key: managed-by
          Value: cloudformation
        - Key: environment
          Value: !Ref Environment
        - Key: project
          Value: "[PROJECT_NAME]"

Outputs:
  DatabaseEndpoint:
    Description: The connection endpoint of the RDS instance
    Value: !GetAtt PrimaryDatabase.Endpoint.Address
    Export:
      Name: !Sub "${AWS::StackName}-DatabaseEndpoint"
```
