#!/usr/bin/env bash
# Generates a Mermaid dependency diagram from flux.yaml files
set -euo pipefail

echo '```mermaid'
echo "flowchart TD"

for flux in k8s/infra/*/flux.yaml k8s/*/flux.yaml; do
  [ -f "$flux" ] || continue

  name=$(yq '.metadata.name' "$flux")
  id=$(echo "$name" | tr '-' '_')
  echo "    ${id}[${name}]"

  deps=$(yq '.spec.dependsOn[].name // ""' "$flux" 2>/dev/null || true)
  for dep in $deps; do
    dep_id=$(echo "$dep" | tr '-' '_')
    echo "    ${id} --> ${dep_id}"
  done
done

echo '```'
