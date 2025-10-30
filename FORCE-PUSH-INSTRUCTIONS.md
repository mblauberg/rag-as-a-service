# Force Push Instructions

**Status:** ✅ Git history cleaned - Ready for force push

---

## Current State

✅ **All API keys removed from git history**
✅ **Secret files removed from tracking**
✅ **Comprehensive .gitignore in place**
✅ **Documentation updated**
✅ **Backup created:** `raas-backup-20251030-115650`

---

## ⚠️ BEFORE Force Pushing

### 1. REVOKE API KEYS (If Not Done Yet)

**OpenAI:** https://platform.openai.com/api-keys
- Revoke key starting with: `sk-proj-zU61...`

**Anthropic:** https://console.anthropic.com/settings/keys
- Revoke key starting with: `sk-ant-api03-wzra...`

### 2. Verify Repository is Private

```bash
# Visit your repository
open https://github.com/mblauberg/rag-as-a-service
```

**Check:** Is it marked as "Private"?
- ✅ **Yes:** Safe to proceed
- ❌ **No:** Make it private first, or assume keys are compromised

### 3. Final Verification

Run these commands to confirm cleanup:

```bash
# Should return nothing
git log --all -S "sk-proj-zU61" --oneline
git log --all -S "sk-ant-api03-wzra" --oneline

# Should show only secret.example.yaml files
git ls-files | grep secret

# Check current commit
git log --oneline | head -5
```

---

## Force Push Commands

### Standard Force Push

```bash
# Push main branch (overwrites remote history)
git push origin main --force

# Push all branches
git push origin --all --force

# Push tags if needed
git push origin --tags --force
```

### What This Does

- **Overwrites** remote repository history
- **Replaces** all commits with cleaned versions
- **Removes** API keys from GitHub permanently
- **Cannot be undone** without backup

---

## After Force Push

### 1. Verify on GitHub

```bash
# Visit your repository
open https://github.com/mblauberg/rag-as-a-service

# Check a few commits to verify keys are gone
# Look at the commit history, especially:
# - security: remove secret.yaml files from tracking
# - Any commits that previously had secret.yaml changes
```

### 2. Clone Fresh Copy (Optional Verification)

```bash
cd /tmp
git clone https://github.com/mblauberg/rag-as-a-service test-clone
cd test-clone

# Verify no keys in history
git log --all -S "sk-proj-zU61" --oneline
git log --all -S "sk-ant-api03-wzra" --oneline

# Should return nothing
cd ..
rm -rf test-clone
```

### 3. Create New API Keys

1. **OpenAI:** Create new key at https://platform.openai.com/api-keys
2. **Anthropic:** Create new key at https://console.anthropic.com/settings/keys

### 4. Update Local Secret Files

```bash
# Copy template
cp infrastructure/k8s/base/generator/secret.example.yaml \
   infrastructure/k8s/base/generator/secret.yaml

# Edit with new keys
# vim/nano infrastructure/k8s/base/generator/secret.yaml

# Verify it's not tracked
git status | grep secret.yaml
# Should show as untracked (??)
```

---

## Troubleshooting

### "Non-fast-forward" Error

```
! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs
```

**Solution:** You must use `--force` because we rewrote history:
```bash
git push origin main --force
```

### "Repository not found"

**Solution:** Verify remote URL:
```bash
git remote -v
# Should show: https://github.com/mblauberg/rag-as-a-service.git
```

### Someone Else is Using the Repo

**Problem:** If others have cloned the repo, their history will be incompatible.

**Solution:**
1. Coordinate with them first
2. They need to delete their local copy
3. They need to fresh clone after your force push

---

## Summary

**What we did:**
- Rewrote 521 commits using git-filter-repo
- Replaced real API keys with placeholders
- Removed secret files from tracking
- Cleaned reflog and garbage collected

**What you need to do:**
1. Revoke old API keys
2. Force push to GitHub
3. Create new API keys
4. Update local secret files

**Final check before push:**
```bash
git log --all -S "sk-proj-zU61" --oneline  # Should return nothing
git log --all -S "sk-ant-api03-wzra" --oneline  # Should return nothing
```

**If both return nothing, you're ready to push!**

---

## The Command

When ready:

```bash
git push origin main --force
```

**That's it!** ✅

---

**Documentation:**
- `API-KEY-CLEANUP-SUMMARY.md` - What was cleaned
- `GIT-REVIEW-REPORT.md` - Detailed security analysis
- Backup: `../raas-backup-20251030-115650/` - Original repository
