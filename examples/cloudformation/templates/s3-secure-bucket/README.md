# s3-secure-bucket (CloudFormation)

A Northwind-standard secure S3 bucket: customer-managed KMS encryption with key rotation, all four
public-access blocks on, TLS-only access enforced by bucket policy, versioning enabled, and lifecycle
tiering of noncurrent versions (STANDARD_IA → GLACIER → expiry). The bucket and KMS key both use
`DeletionPolicy: Retain` so a stack deletion never destroys data.

## Deploy

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name dev-analytics-s3-secure \
  --parameter-overrides file://parameters/dev.json \
  --tags managed-by=cloudformation environment=dev team=analytics project=northwind-platform \
  --capabilities CAPABILITY_NAMED_IAM
```

For staging/prod, generate and review a change set first:

```bash
aws cloudformation create-change-set \
  --template-body file://template.yaml \
  --stack-name prod-orders-s3-secure \
  --change-set-name review \
  --parameters file://parameters/prod.json \
  --change-set-type CREATE
# review, then:
aws cloudformation execute-change-set --stack-name prod-orders-s3-secure --change-set-name review
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `Environment` | String | — | `dev` / `staging` / `prod`. |
| `CostCenter` | String | — | Billing code, format `CC-NNNN`. |
| `Team` | String | — | Owning team (`orders`, `analytics`, …). |
| `Project` | String | `northwind-platform` | Project identifier. |
| `DataClassification` | String | — | `public` / `internal` / `confidential` / `restricted`. |
| `TransitionToIADays` | Number | `30` | Days before noncurrent versions move to STANDARD_IA. |
| `TransitionToGlacierDays` | Number | `90` | Days before noncurrent versions move to GLACIER. |
| `NoncurrentExpirationDays` | Number | `365` | Days before noncurrent versions are expired. |
| `KmsKeyDeletionWindowDays` | Number | `30` | KMS key deletion waiting period (7–30). |

## Outputs

| Output | Description | Exported |
|--------|-------------|----------|
| `BucketName` | Generated bucket name. | ✅ `${StackName}-BucketName` |
| `BucketArn` | Bucket ARN. | ✅ `${StackName}-BucketArn` |
| `BucketRegionalDomainName` | Regional domain name. | — |
| `KmsKeyArn` | ARN of the customer-managed KMS key. | ✅ `${StackName}-KmsKeyArn` |

## Security properties

- **Encryption at rest**: SSE-KMS with a customer-managed key (`BucketKeyEnabled` to cut KMS costs).
- **No public access**: all four `PublicAccessBlockConfiguration` flags `true`; ACLs disabled via `BucketOwnerEnforced`.
- **TLS only**: bucket policy denies any request with `aws:SecureTransport = false`.
- **Durability**: versioning enabled; `DeletionPolicy: Retain` on bucket and key.

## Out of scope

- **Cross-region replication** (Northwind requires it for prod critical buckets) — adds a replication
  IAM role + destination bucket; deploy it as a follow-up stack or extend this template behind an
  `IsProd` condition.
- **Server access logging / Object Lock** — add per workload when required.

## Validation

```bash
cfn-lint template.yaml
aws cloudformation validate-template --template-body file://template.yaml
```
