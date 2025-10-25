#!/bin/bash
set -e

echo "🧹 Cleaning up RAAS from local Kubernetes..."

# Delete all resources
kubectl delete -k ../overlays/local/ || true

# Wait a bit for cleanup
sleep 5

# Verify cleanup
echo ""
echo "📊 Remaining resources in raas namespace:"
kubectl get all -n raas || echo "Namespace deleted"

echo ""
echo "✅ Cleanup complete!"
