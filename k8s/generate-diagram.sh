#!/usr/bin/env bash
# Generates a Mermaid dependency diagram from flux.yaml files
set -euo pipefail

echo '```mermaid'
echo "flowchart TD"

files=("k8s/infra/flux.yaml")
for f in k8s/*/flux.yaml; do
  [[ "$f" == k8s/infra/flux.yaml ]] && continue
  files+=("$f")
done

for flux in "${files[@]}"; do
  [ -f "$flux" ] || continue

  count=$(yq 'document_index' "$flux" | wc -l)

  for i in $(seq 0 $((count - 1))); do
    name=$(yq "select(document_index == $i) | .metadata.name" "$flux")
    id=$(echo "$name" | tr '-' '_')
    echo "    ${id}[${name}]"

    deps=$(yq "select(document_index == $i) | .spec.dependsOn[].name // \"\"" "$flux" 2>/dev/null || true)
    for dep in $deps; do
      dep_id=$(echo "$dep" | tr '-' '_')
      echo "    ${id} --> ${dep_id}"
    done
  done
done

echo '```'
