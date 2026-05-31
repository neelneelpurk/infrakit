# InfraKit Examples

Three complete, end-to-end walkthroughs showing every file InfraKit produces when you take an
infrastructure resource from "I need this" to "ready to publish."

| Walkthrough | IaC Tool | Scenario | Path |
|-------------|----------|----------|------|
| [Terraform](terraform/) | Terraform 1.7+ | AWS S3 secure-bucket module with KMS, lifecycle, optional CRR | [`examples/terraform/`](terraform/) |
| [Crossplane](crossplane/) | Crossplane v1.15+ | `XPostgreSQLInstance` XR wrapping AWS RDS via `provider-aws-rds` | [`examples/crossplane/`](crossplane/) |
| [CloudFormation](cloudformation/) | AWS CloudFormation | S3 secure-bucket template — KMS, public access blocked, TLS-only, lifecycle | [`examples/cloudformation/`](cloudformation/) |

Each example contains the `.infrakit/` config (context, coding-style, tagging-standard), a
single track under `.infrakit_tracks/tracks/`, and the actual deliverable (the `.tf` module, the
Crossplane Composition YAML, or the CloudFormation `template.yaml`).

Read the per-example README inside each directory for the full file map and a recommended
reading order.
