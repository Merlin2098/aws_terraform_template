# PowerShell JSON and YAML Handling

## When to use

- Reading or writing Terraform variable files, Kubernetes manifests, or CI/CD config
- Parsing AWS CLI / `terraform output -json` responses
- Transforming configuration between formats (JSON ↔ YAML, JSON ↔ PSCustomObject)

---

## JSON

### Parse

```powershell
# From file
$config = Get-Content -Path 'config.json' -Raw | ConvertFrom-Json

# From command output (e.g. terraform, aws cli)
$outputs = terraform -chdir=infra output -json | ConvertFrom-Json
$bucket  = $outputs.artifact_bucket_name.value
```

### Serialize

```powershell
$obj = [PSCustomObject]@{
    project     = 'my-app'
    environment = 'dev'
    tags        = @{ Owner = 'team'; ManagedBy = 'Terraform' }
}

# -Depth controls nesting; default is 2 — increase for nested objects
$obj | ConvertTo-Json -Depth 10 | Out-File 'output.json' -Encoding utf8
```

### PS 7+ enhancements

```powershell
# -AsHashtable makes keys accessible via $h['key'] (PS 7+)
$hash = Get-Content 'config.json' | ConvertFrom-Json -AsHashtable
```

### Gotchas

| Trap | Fix |
|---|---|
| Default `-Depth 2` truncates nested objects | Always pass `-Depth 10` (or required depth) |
| BOM in UTF-8 files breaks `ConvertFrom-Json` | Use `-Encoding utf8NoBOM` when writing |
| `null` JSON values become empty string in PS 5.1 | Use PS 7+ or check `$val -eq $null` carefully |
| Arrays of 1 element collapse to single object | Wrap with `@(...)` after parse |

---

## YAML

PowerShell has no built-in YAML support. Options in order of preference:

### Option 1 — `powershell-yaml` module (PS Gallery)

```powershell
# Install once
Install-Module -Name powershell-yaml -Scope CurrentUser -Force

# Parse
$yaml = Get-Content 'values.yaml' -Raw | ConvertFrom-Yaml

# Serialize
$yaml | ConvertTo-Yaml | Out-File 'output.yaml' -Encoding utf8NoBOM
```

### Option 2 — delegate to Python (no extra PS module needed)

```powershell
$parsed = python -c "import sys, yaml, json; print(json.dumps(yaml.safe_load(sys.stdin)))" `
    < values.yaml | ConvertFrom-Json
```

### Option 3 — yq CLI (cross-platform)

```powershell
$value = yq '.image.tag' values.yaml
```

Use `powershell-yaml` when the module is available; fall back to Python or `yq` otherwise. Document the chosen approach in the script header.

---

## Common patterns

### Merge two JSON configs (override pattern)

```powershell
function Merge-Config {
    param($Base, $Override)
    $merged = $Base | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    foreach ($key in ($Override | Get-Member -MemberType NoteProperty).Name) {
        $merged.$key = $Override.$key
    }
    $merged
}

$base     = Get-Content 'base.json'     | ConvertFrom-Json
$override = Get-Content 'override.json' | ConvertFrom-Json
$final    = Merge-Config -Base $base -Override $override
```

### Read Terraform outputs safely

```powershell
$raw = terraform -chdir=infra output -json
if ($LASTEXITCODE -ne 0) { throw "terraform output failed" }
$outputs = $raw | ConvertFrom-Json
```

## Best practices

- Always use `-Depth 10` with `ConvertTo-Json` for nested config objects
- Write JSON files with `-Encoding utf8NoBOM` to avoid BOM issues in Linux tools
- Validate after parse: check expected keys exist before accessing them
- For CI pipelines that also run on Linux, prefer `yq` or Python YAML over PS modules

## Avoid

- Using `ConvertTo-Json` without `-Depth` on objects deeper than 2 levels
- Installing `powershell-yaml` in CI without pinning the version
- Editing YAML by string concatenation — always parse and re-serialize
