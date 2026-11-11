# AWS infrastructure

A VPC across three availability zones and an EKS cluster with one managed node
group, built from the community `terraform-aws-modules`.

CI runs `terraform fmt -check` and `terraform validate` on every change. CI
does **not** run `plan` or `apply`: the repository has no AWS credentials, and
this configuration has not been applied from here. Treat it as a reviewed
starting point, and read the plan before you apply it.

## Usage

State lives in S3 with native lock files. The bucket is passed at init time so
no account-specific values are committed:

```bash
terraform init \
  -backend-config="bucket=<your-state-bucket>" \
  -backend-config="key=platform-reference/terraform.tfstate" \
  -backend-config="region=us-east-2"
```

```bash
cp example.tfvars terraform.tfvars
```

```bash
terraform plan
```

After `terraform apply`, the `kubeconfig_command` output prints the command
that configures `kubectl`. Then bootstrap Argo CD as described in the top-level
README.

## Cost

The defaults favour a cheap demo over availability: Spot nodes and a single
NAT gateway. The fixed parts are the EKS control plane, two `t3.medium`-class
nodes and one NAT gateway. Run `terraform destroy` when you are done.

For production, set `single_nat_gateway = false` and
`node_capacity_type = "ON_DEMAND"`.
