# DELIBERATELY INSECURE — eval negative fixture. Do NOT use as a real module.
# This exists to prove the scorer actually fails bad output. It violates every
# secure-default InfraKit checks for: public, unencrypted, hardcoded credential,
# untagged, no versioning, no TLS policy, force_destroy = true.

resource "aws_s3_bucket" "bad" {
  bucket        = "my-totally-public-bucket"
  acl           = "public-read"
  force_destroy = true
}

resource "aws_db_instance" "bad" {
  engine              = "postgres"
  instance_class      = "db.t3.micro"
  username            = "admin"
  password            = "hunter2"
  publicly_accessible = true
  skip_final_snapshot = true
}
