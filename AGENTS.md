# AGENTS.md

## 🎯 Purpose

This repository is an AWS + Terraform data engineering template.

The agent should assist in building:

* Data pipelines (Python, SQL)
* Infrastructure (Terraform)
* Config-driven systems

---

## 🧠 Knowledge

Use:

* `ai/skills/` → patterns and best practices
* `skills.yaml` → index

Skills are guidance only, not executable logic.

---

## 🔄 Usage Pattern

When assisting:

1. Understand the objective
2. Identify relevant skills (based on task and skill naming)
3. Apply patterns (adapt, don’t enforce)
4. Generate simple, explicit solutions
5. Validate against repo principles
6. Iterate incrementally

---

## 🧠 Skill Usage

The agent should:

* Discover relevant skills automatically from `ai/skills/`
* Match tasks with skill names (e.g.,  *testing* ,  *ci_cd* ,  *mocks* ,  *glue* ,  *terraform* )
* Use skills as guidance without requiring explicit user invocation

The agent must NOT:

* require explicit skill invocation
* enforce rigid mappings between tasks and skills
* create skill composition or orchestration logic

---

## ⚙️ Rules

### ❌ Never (without approval)

* `terraform apply`
* `terraform destroy`
* Modify infrastructure state
* Overwrite data or artifacts

### ⚠️ Ask before

* IAM changes
* Terraform module changes
* Data contract updates

---

## 🧱 Principles

* Separation of concerns (infra / code / config)
* SQL separate from Python
* Config-driven pipelines
* Contracts-first validation
* Prefer simple over complex

---

## 🚀 Execution

Use explicit commands only:

* `make package`
* Terraform commands directly, when intentionally managing infrastructure

Do not introduce hidden automation.

---

## 🔒 Constraints

The agent must NOT:

* create orchestration frameworks
* define skill composition
* introduce meta-systems
* recreate Tinker-like behavior

---

## 📁 Existing Code Awareness

Before generating any new file or artifact, the agent must:

1. Search the repository for existing implementations
2. Prefer modifying or extending existing files over creating new ones
3. Avoid duplicating:
   * Terraform modules
   * ETL jobs
   * SQL transformations
   * Config files

If similar functionality exists:
→ reuse or refactor instead of creating new files

Only create new files when:

* no equivalent exists
* or the user explicitly requests it

---

## 🔥 Philosophy

Simple. Explicit. Reproducible.

AI is a helper, not the system.
