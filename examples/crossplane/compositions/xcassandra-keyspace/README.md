# xcassandra-keyspace

A Crossplane composite resource that provisions an **Amazon Keyspaces (for Apache Cassandra)**
keyspace and table with a per-keyspace customer-managed KMS key, env-defaulted point-in-time
recovery, and the platform's mandatory tags. Product teams claim `CassandraKeyspace` from their
team namespace; the platform team owns this Composition.

The Composition uses **Pipeline mode with `function-go-templating`** (the project's standard
pipeline function) plus `function-auto-ready`.

---

## Usage

```yaml
apiVersion: database.platform.acme.com/v1alpha1
kind: CassandraKeyspace
metadata:
  name: telemetry
  namespace: data
spec:
  parameters:
    environment: prod
    teamName: data
    costCenter: CC-1042
    keyspaceName: device_telemetry
```

Amazon Keyspaces authenticates with SigV4 (typically via IRSA), so there is **no connection
secret and no password**. The composite publishes the keyspace name, table name and contact
point as `status` fields instead; applications connect to `cassandra.<region>.amazonaws.com:9142`
over TLS using their own IAM identity.

Two example claims are bundled:

- [`examples/claim-dev.yaml`](examples/claim-dev.yaml) — a minimal dev claim. Point-in-time
  recovery falls back to its env default (`false`).
- [`examples/claim-prod.yaml`](examples/claim-prod.yaml) — a realistic prod claim. Point-in-time
  recovery falls back to its env default (`true`).

---

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `environment` | string | yes | — | `dev` / `staging` / `prod` |
| `teamName` | string | yes | — | `payments` / `data` / `frontend` / `mobile` / `platform` |
| `costCenter` | string | yes | — | `CC-NNNN` |
| `keyspaceName` | string | yes | — | CQL keyspace name (lowercase, digits, underscores; no dashes) |
| `region` | string | no | `us-east-1` | AWS region |
| `tableName` | string | no | `events` | CQL table name |
| `pointInTimeRecovery` | bool | no | env-default | prod = `true`, else `false`; override permitted |

The keyspace is created as `{environment}_{teamName}_{keyspaceName}` — underscores, never dashes,
because Cassandra Query Language identifiers cannot contain a hyphen.

---

## Status

| Field | Description |
|-------|-------------|
| `keyspaceName` | Keyspace name as created in Amazon Keyspaces |
| `tableName` | Table name created within the keyspace |
| `contactPoint` | `cassandra.<region>.amazonaws.com` |
| `kmsKeyArn` | ARN of the customer-managed KMS key |
| `ready` | True when the KMS key, keyspace and table are all Ready |

---

## Constraints (non-overridable)

- `encryptionSpecification.type: CUSTOMER_MANAGED_KMS_KEY` — never the default AWS-owned key.
- `enableKeyRotation: true` on the KMS key, 30-day deletion window.
- `capacitySpecification.throughputMode: PAY_PER_REQUEST` — on-demand capacity, nothing to over-provision.
- `deletionPolicy: Orphan` on the table — stateful data is never auto-deleted with the composition.
- Required tags on every managed resource, sourced from claim labels and parameters.

---

## Validation

Full render (requires the `crossplane` CLI and the function images cached):

```bash
crossplane render \
  examples/claim-prod.yaml \
  composition.yaml \
  functions.yaml
```

(`functions.yaml` declares `function-go-templating` and `function-auto-ready` for
`crossplane render`. The cluster itself loads the functions from the platform's package
registry, not from this file.)

YAML syntactic validation (no cluster needed):

```bash
python3 -c 'import yaml,sys; [list(yaml.safe_load_all(open(f))) for f in sys.argv[1:]]' \
  definition.yaml composition.yaml examples/claim-dev.yaml examples/claim-prod.yaml
```

---

## Providers

This composition manages resources from:

- [`upbound/provider-aws-keyspaces`](https://marketplace.upbound.io/providers/upbound/provider-aws-keyspaces) — `Keyspace`, `Table`
- [`upbound/provider-aws-kms`](https://marketplace.upbound.io/providers/upbound/provider-aws-kms) — `Key`

Every `apiVersion` and field name was verified against [`doc.crds.dev`](https://doc.crds.dev) and
the Upbound provider schemas before the YAML was written.
