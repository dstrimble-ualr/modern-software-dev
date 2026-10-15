#!/usr/bin/env bash
# Print a kubeconfig for the github-deployer service account (k8s/bootstrap/deployer.yaml).
# It can only manage the app in the python-example namespace.
#
# Run as a cluster admin, after `kubectl apply -f k8s/bootstrap/`, and pipe it straight
# into the GitHub secret so the token never lands on disk:
#
#   scripts/deployer_kubeconfig.sh | gh secret set KUBECONFIG --env production
#
# A pipe sends whatever came out even if this script fails, so if it prints an error,
# fix that and run the whole line again.
set -euo pipefail

NAMESPACE=python-example
SECRET=github-deployer-token

if ! kubectl -n "$NAMESPACE" get secret "$SECRET" > /dev/null 2>&1; then
  echo "No $NAMESPACE/$SECRET secret. Run 'kubectl apply -f k8s/bootstrap/' first." >&2
  exit 1
fi

server=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
ca=$(kubectl -n "$NAMESPACE" get secret "$SECRET" -o jsonpath='{.data.ca\.crt}')
token=$(kubectl -n "$NAMESPACE" get secret "$SECRET" -o jsonpath='{.data.token}' | base64 --decode)

cat <<EOF
apiVersion: v1
kind: Config
clusters:
  - name: cluster
    cluster:
      server: $server
      certificate-authority-data: $ca
users:
  - name: github-deployer
    user:
      token: $token
contexts:
  - name: github-deployer
    context:
      cluster: cluster
      user: github-deployer
      namespace: $NAMESPACE
current-context: github-deployer
EOF
