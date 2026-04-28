# Terraform Discovery & Bulk Import Pattern

## When to use

- Terraform >= 1.14
- Provider supports list resources
- Large-scale infrastructure discovery

## Core idea

Use Terraform Search (`list` blocks) to discover resources and generate import configuration.

## Workflow

1. Verify provider supports list resources
2. Create `.tfquery.hcl` file
3. Run `terraform query`
4. Generate config (`-generate-config-out`)
5. Clean and refactor generated code
6. Run plan and apply

## Key concepts

- list block → resource discovery
- query files → search definitions
- generated config → import + resource blocks

## Best practices

- Start with broad queries, then filter
- Use limit to control output
- Remove computed attributes after generation
- Replace hardcoded values with variables

## Multi-region pattern

- Use for_each in queries
- Iterate regions dynamically

## Advantages

- Faster than manual import
- Scales to many resources
- Integrated with Terraform

## Limitations

- Requires provider support
- Generated code needs cleanup

## Avoid

- Using without checking provider support
- Applying generated config without review
- Keeping generated code as-is
