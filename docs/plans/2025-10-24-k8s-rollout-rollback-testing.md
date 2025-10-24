# Kubernetes Rollout and Rollback Testing Design

**Date**: 2025-10-24
**Status**: Approved
**Target**: API service deployment in raas namespace

## Overview

This design describes an automated testing script to verify Kubernetes rollout and rollback mechanisms work correctly for the RAAS platform. The script tests both successful deployment rollouts and failure recovery through rollback, without modifying application code or risking service availability.

## Goals

1. Verify successful rolling updates complete without downtime
2. Test rollback recovery when deployments fail
3. Ensure service remains available throughout all operations
4. Provide repeatable, safe testing that doesn't break implementation

## Non-Goals

- Production deployment automation
- Comprehensive CI/CD pipeline integration
- Multi-service orchestrated rollouts
- Performance or load testing during rollouts

## Design Decisions

### Core Strategy: Safe, Non-Breaking Operations

The script uses Kubernetes built-in mechanisms without code changes:

1. **Successful Rollout**: Use `kubectl rollout restart` to trigger controlled rollout with same image
2. **Failure Simulation**: Patch deployment with non-existent image tag (triggers ImagePullBackOff)
3. **Rollback**: Use `kubectl rollout undo` to restore previous working state

**Safety Guarantees**:
- No application code modifications
- Kubernetes maintains old pods when new ones fail
- Service remains available (assumes replica count > 1)
- Script can be interrupted safely at any point
- Automatic cleanup on failure

### Test Target: API Service

Selected because:
- Has well-defined health endpoints (`/api/v1/health`)
- Critical path component (good representative test)
- Easy to verify functionality through HTTP checks

## Test Flow

### Phase 1: Baseline Verification

**Purpose**: Establish known-good starting state

**Operations**:
1. Check cluster connectivity (`kubectl cluster-info`)
2. Verify namespace and deployment exist
3. Record current revision number
4. Capture current image tag
5. Test health endpoint accessibility
6. Save deployment state for recovery

**Success Criteria**: All checks pass, service responding

### Phase 2: Successful Rollout Test

**Purpose**: Verify rolling updates work correctly

**Operations**:
1. Execute `kubectl rollout restart deployment/api -n raas`
2. Monitor with `kubectl rollout status` (2-minute timeout)
3. Verify new pods become ready
4. Confirm revision number increments
5. Test health endpoint remains responsive

**Success Criteria**:
- Rollout completes successfully
- Revision increments by 1
- Health checks pass throughout

### Phase 3: Failed Deployment Simulation

**Purpose**: Test system behavior when bad deployments occur

**Operations**:
1. Patch deployment image to `raas-api:nonexistent-v999`
2. Watch for ImagePullBackOff status (max 5 minutes)
3. Verify old pods remain healthy
4. Confirm service endpoint stays responsive
5. Check that revision number increments but pods don't update

**Success Criteria**:
- ImagePullBackOff appears for new pods
- Old pods continue running
- Service remains available
- Health checks continue passing

### Phase 4: Rollback Recovery

**Purpose**: Verify rollback restores working state

**Operations**:
1. Execute `kubectl rollout undo deployment/api -n raas`
2. Monitor rollback completion (2-minute timeout)
3. Verify pods return to working state
4. Test health endpoint
5. Confirm revision returns to previous working number

**Success Criteria**:
- Rollback completes successfully
- All pods become ready
- Health checks pass
- Service fully operational

## Implementation Specifications

### Script Details

- **Location**: `tests/integration/test_k8s_rollout_rollback.sh`
- **Language**: Bash (portable, no dependencies)
- **Permissions**: Executable (`chmod +x`)

### Health Check Function

```bash
check_api_health() {
  # Port-forward to service in background
  kubectl port-forward -n raas svc/api 8000:8000 &
  PF_PID=$!
  sleep 3

  # Test health endpoint with retry logic
  for i in {1..3}; do
    if curl -sf http://localhost:8000/api/v1/health >/dev/null; then
      kill $PF_PID 2>/dev/null
      return 0
    fi
    sleep 2
  done

  kill $PF_PID 2>/dev/null
  return 1
}
```

### Timeouts and Retry Logic

- **Rollout status**: 2-minute timeout
- **ImagePullBackOff detection**: 5-minute maximum wait
- **Health checks**: 3 attempts with 2-second delays between retries
- **Port-forward startup**: 3-second grace period

### Error Handling and Cleanup

**Trap handler**:
```bash
cleanup() {
  # Kill any background port-forwards
  # Restore original deployment if needed
  # Print final status
}
trap cleanup EXIT
```

**Failure scenarios handled**:
- Cluster unreachable
- Namespace/deployment missing
- Health checks failing
- Timeout exceeded
- Script interruption (Ctrl+C)

### Output Format

**Color-coded results**:
- Green (✓): Success
- Red (✗): Failure
- Yellow (ℹ): Information

**Example output**:
```
=== Phase 1: Baseline Verification ===
✓ Cluster accessible
✓ Current revision: 5
✓ Image: raas-api:latest
✓ Health check passed

=== Phase 2: Successful Rollout ===
ℹ Initiating rollout restart...
✓ Rollout completed
✓ New revision: 6
✓ Health check passed

=== Phase 3: Failed Deployment Simulation ===
ℹ Deploying non-existent image tag...
✓ ImagePullBackOff detected
✓ Old pods still running
✓ Service still healthy

=== Phase 4: Rollback Recovery ===
ℹ Initiating rollback...
✓ Rollback completed
✓ Revision restored to: 5
✓ Health check passed

=== TEST SUMMARY ===
✓ All phases passed
```

## Testing and Validation

### Prerequisites

- Kind cluster running with raas namespace
- API deployment with at least 1 replica
- kubectl configured and authenticated

### Running the Script

```bash
./tests/integration/test_k8s_rollout_rollback.sh
```

### Expected Duration

- Total runtime: 5-8 minutes
- Phase 1: 10-20 seconds
- Phase 2: 1-2 minutes
- Phase 3: 1-2 minutes
- Phase 4: 1-2 minutes

### Success Indicators

- All phases show green checkmarks
- No service downtime reported
- Revision numbers change as expected
- Health checks pass throughout

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Script leaves deployment in bad state | Medium | Cleanup trap handler restores on exit |
| Service becomes unavailable | High | Kubernetes keeps old pods during failures |
| Script hangs indefinitely | Low | Timeouts on all kubectl wait operations |
| Port conflicts on 8000 | Low | Script kills port-forward on cleanup |

## Future Enhancements

If needed later (YAGNI for now):
- Test multiple services concurrently
- Integrate with CI/CD pipeline
- Add Prometheus metrics verification
- Test HPA behavior during rollouts
- Canary deployment testing
