#!/bin/bash
set -e

echo "========================================="
echo "Testing Rollout and Rollback (Type I Requirement)"
echo "========================================="

NAMESPACE="raas"
DEPLOYMENT="api"

echo ""
echo "Current Deployment Status:"
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT

echo ""
echo "Current Deployment Image:"
kubectl get deployment/$DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}'
echo ""

echo ""
echo "Step 1: Triggering a rollout by adding an annotation..."
kubectl annotate deployment/$DEPLOYMENT -n $NAMESPACE \
  kubernetes.io/change-cause="Testing rollout functionality for Type I project" \
  --overwrite

# Trigger a rollout by updating an environment variable
kubectl set env deployment/$DEPLOYMENT -n $NAMESPACE \
  ROLLOUT_TEST="$(date +%s)" \
  --overwrite

echo ""
echo "Step 2: Watching the rollout progress..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE

echo ""
echo "Deployment History:"
kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE

echo ""
echo "Current Pods after rollout:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT -o wide

echo ""
echo "Step 3: Testing rollback functionality..."
echo "Rolling back to previous revision..."
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

echo ""
echo "Watching the rollback progress..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE

echo ""
echo "Deployment History after rollback:"
kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE

echo ""
echo "Current Pods after rollback:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT -o wide

echo ""
echo "========================================="
echo "Rollout and Rollback Test Complete!"
echo "========================================="
echo ""
echo "Key Observations for Presentation:"
echo "  1. RollingUpdate strategy ensures zero downtime"
echo "  2. New pods created before old ones terminated"
echo "  3. Rollback to previous revision works seamlessly"
echo "  4. RevisionHistoryLimit preserves deployment history"
echo ""
echo "Commands demonstrated:"
echo "  - kubectl rollout status: Monitor deployment progress"
echo "  - kubectl rollout history: View revision history"
echo "  - kubectl rollout undo: Rollback to previous version"
echo "  - kubectl set env: Trigger new rollout"
echo ""
