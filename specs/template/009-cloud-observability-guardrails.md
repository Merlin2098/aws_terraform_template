# SPEC-009 — AWS/Terraform Operational Guardrails & Observability Standard

---

# 1. Purpose

Define mandatory operational standards for AWS/Terraform projects in order to:

* Reduce operational failures
* Improve observability and debugging
* Prevent infrastructure drift
* Protect Terraform state integrity
* Standardize smoke testing
* Improve cost governance
* Increase reproducibility
* Establish reusable operational scripts for humans and AI agents

This SPEC is intended to be integrated into:

* AI agent policies
* Skills
* Project templates
* Terraform foundations
* CI/CD pipelines
* Framework guardrails

---

# 2. Core Principles

## 2.1 Infrastructure as Code First

All infrastructure must be declared in Terraform.

Manual console changes are only allowed for:

* temporary debugging
* emergency remediation
* controlled troubleshooting

Any manual modification must later be reconciled back into Terraform.

---

## 2.2 Observability by Default

Every deployable service must provide:

* logs
* outputs
* debugging visibility
* post-run traceability

---

## 2.3 Validation Before Deployment

Every infrastructure deployment must include automated validation scripts for:

* IAM validation
* smoke checks
* tagging validation
* budget validation
* resource existence validation

---

## 2.4 Reproducibility

Operational validation must rely on reusable scripts instead of AWS Console interactions.

---

# 3. Standard Operational Script Structure

All AWS operational scripts must be generated under:

<pre class="overflow-visible! px-0!" data-start="1521" data-end="1543"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>tests/aws/</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Recommended structure:

<pre class="overflow-visible! px-0!" data-start="1569" data-end="2011"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>tests/aws/</span><br/><span>├── precheck/</span><br/><span>│   ├── validate_iam.ps1</span><br/><span>│   ├── validate_tags.ps1</span><br/><span>│   ├── validate_budget.ps1</span><br/><span>│   └── smoke_resources.ps1</span><br/><span>│</span><br/><span>├── logs/</span><br/><span>│   ├── download_cloudwatch_logs.ps1</span><br/><span>│   ├── download_stepfunctions_logs.ps1</span><br/><span>│   └── export_pipeline_outputs.ps1</span><br/><span>│</span><br/><span>├── smoke/</span><br/><span>│   ├── smoke_s3.ps1</span><br/><span>│   ├── smoke_glue.ps1</span><br/><span>│   ├── smoke_lambda.ps1</span><br/><span>│   └── smoke_athena.ps1</span><br/><span>│</span><br/><span>├── gitbash/</span><br/><span>│   └── equivalent_linux_scripts.sh</span><br/><span>│</span><br/><span>└── README.md</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 4. Mandatory Validations

# 4.1 IAM Validation

IAM validation scripts are mandatory.

Scripts must validate:

* IAM Roles
* Trust Policies
* Attached Policies
* AssumeRole permissions
* Policy attachments
* Permissions boundaries

Mandatory execution before deployment:

<pre class="overflow-visible! px-0!" data-start="2292" data-end="2347"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>.\</span><span class="ͼ11">tests</span><span>\</span><span class="ͼ11">aws</span><span>\</span><span class="ͼ11">precheck</span><span>\</span><span class="ͼ11">validate_iam</span><span>.</span><span class="ͼ11">ps1</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 4.2 Resource Smoke Validation

All critical resources must have smoke validation scripts.

Minimum requirements:

| Resource       | Validation             |
| -------------- | ---------------------- |
| S3             | bucket exists + access |
| Lambda         | invoke test            |
| Glue           | job visibility         |
| Athena         | query execution        |
| Step Functions | state machine exists   |
| CloudWatch     | log group exists       |
| IAM            | role assumable         |

---

# 4.3 Tag Validation

All resources must include mandatory tags.

Minimum required tags:

<pre class="overflow-visible! px-0!" data-start="2815" data-end="2987"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>tags = {</span><br/><span>  Project     = var.project_name</span><br/><span>  Environment = var.environment</span><br/><span>  Owner       = var.owner</span><br/><span>  ManagedBy   = "Terraform"</span><br/><span>  CostCenter  = var.cost_center</span><br/><span>}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 4.4 Budget Validation

Every project must include:

* at least one AWS Budget
* cost alerting
* logical association through tagging

## Rule

No deployable environment should exist without budget governance.

---

# 5. Logging & Observability

# 5.1 Explicit CloudWatch Logging

All supported AWS services must explicitly declare:

* CloudWatch Log Groups
* retention policies
* outputs
* permissions

Never rely on implicit AWS-generated logs.

---

# 5.2 Explicit Resource Declaration

Always explicitly declare:

* log groups
* IAM roles
* IAM policies
* outputs
* retention settings

---

# 5.3 Default Retention Standard

For demos, labs, and prototypes:

<pre class="overflow-visible! px-0!" data-start="3657" data-end="3685"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>7 days retention</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

For production:

* defined by business requirements
* compliance requirements
* audit policies
* customer constraints

---

# 6. CloudTrail Requirements

CloudTrail must be enabled for:

* troubleshooting
* auditability
* IAM debugging
* deployment tracing
* post-pipeline analysis

---

# 7. Log & Output Extraction

The project must provide reusable scripts to download:

* CloudWatch Logs
* Step Functions execution history
* Terraform outputs
* Athena query results
* Glue logs

Supported interfaces:

* PowerShell
* AWS CLI
* Git Bash

---

# 8. Terraform Governance

# 8.1 Never Delete Terraform State

The Terraform state file must never be manually deleted.

Forbidden operation:

<pre class="overflow-visible! px-0!" data-start="4376" data-end="4408"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼ10">rm</span><span> terraform.tfstate</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Risks include:

* orphaned infrastructure
* resource drift
* destructive redeployments
* infrastructure inconsistency

---

# 8.2 Drift Management Standard

If infrastructure is modified manually through the AWS Console:

## Required process

1. Detect drift
2. Remove resource from Terraform state

<pre class="overflow-visible! px-0!" data-start="4710" data-end="4740"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>terraform state </span><span class="ͼ10">rm</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

3. Re-import resource

<pre class="overflow-visible! px-0!" data-start="4765" data-end="4793"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>terraform import</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

4. Update Terraform code

---

# 8.3 Versioning Policy

## Rule

S3 versioning must NOT be enabled by default.

It must be:

* explicitly requested
* documented
* justified

## Rationale

Avoid:

* hidden costs
* destroy complexity
* storage accumulation
* demo cleanup issues

---

# 9. Mandatory Outputs

Every Terraform module must expose minimum outputs:

<pre class="overflow-visible! px-0!" data-start="5155" data-end="5243"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼs ͼ16"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>output "resource_arn" {}</span><br/><span>output "resource_name" {}</span><br/><span>output "log_group_name" {}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# 10. AI Agent Operational Policies

# AI Agents MUST:

* generate smoke test scripts
* validate IAM before apply
* generate operational outputs
* declare CloudWatch logs explicitly
* validate tagging
* validate budgets
* provide reusable debugging scripts

---

# AI Agents MUST NOT:

* delete Terraform state
* enable versioning by default
* assume implicit IAM permissions
* depend exclusively on AWS Console
* create untagged resources
* omit retention policies

---

# 11. Recommended Skills

# Skill: aws_smoke_testing

Responsibilities:

* smoke validation generation
* resource health validation
* operational testing

---

# Skill: terraform_observability

Responsibilities:

* CloudWatch integration
* retention policy management
* debugging outputs
* operational logging

---

# Skill: terraform_governance

Responsibilities:

* tagging enforcement
* budget enforcement
* drift management
* lifecycle governance

---

# 12. Definition of Done (DoD)

An AWS/Terraform project is considered operationally compliant only if:

* [ ] All resources include mandatory tags
* [ ] Budgets are configured
* [ ] Smoke test scripts exist
* [ ] IAM validation scripts exist
* [ ] CloudWatch logs are explicitly declared
* [ ] Outputs are declared
* [ ] Retention policies are configured
* [ ] Log download scripts exist
* [ ] Drift management process is documented
* [ ] Terraform state is protected
* [ ] Versioning decisions are explicitly documented

---

# 13. Framework Integration

This SPEC should integrate with:

* `agents.md`
* `claude.md`
* `skills/aws/`
* `policies/aws/`
* Terraform base templates
* Makefiles
* pre-commit hooks
* CI/CD pipelines

---

# 14. Expected Outcomes

This standard is expected to provide:

* Faster debugging
* Lower operational risk
* Better observability
* Reduced infrastructure drift
* Improved reproducibility
* Better AI-agent compatibility
* Lower dependency on AWS Console
* Stronger DevOps/SRE operational maturity
