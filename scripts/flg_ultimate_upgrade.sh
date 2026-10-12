#!/bin/bash
echo "🚀 [FLG OS] Initializing Ultimate Local Upgrade (Safety + Pipelines + Studio 8K Enhancements)..."

# 1. Local Safety Plan & Isolated Trash Bin
mkdir -p ~/.flg_trash/{typos,build_failures,drafts,secrets}
echo "✅ Local trash bin active at ~/.flg_trash"

if ! grep -q ".flg_trash" ~/.gitignore_global 2>/dev/null; then
    echo ".flg_trash/" >> ~/.gitignore_global
    git config --global core.excludesfile ~/.gitignore_global
    echo "✅ Trash added to global gitignore."
fi

# 2. Pre-Commit Token Interception Hook
if [ -d ".git" ]; then
    cat << 'HOOK' > .git/hooks/pre-commit
#!/bin/bash
SECRETS=$(grep -E "(GITHUB_TOKEN|GH_PAT|ghp_[A-Za-z0-9]{36})" -r src/ 2>/dev/null)
if [ -n "$SECRETS" ]; then
    echo "❌ [SECURITY BLOCK] Hardcoded tokens detected in src/!"
    grep -lE "(GITHUB_TOKEN|GH_PAT|ghp_[A-Za-z0-9]{36})" -r src/ | xargs -I {} mv {} ~/.flg_trash/secrets/
    exit 1
fi
exit 0
HOOK
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit security hook installed."
fi

# 3. GitHub Agentic Workflow Local Spec Stub (gh-aw)
mkdir -p .github/workflows
cat << 'SPEC' > .github/workflows/flg-pipeline-audit.md
---
name: FLG Pipeline Audit (Local Spec)
on: [push]
---
# FLG Pipeline Guard
Local tracking structure for CodeRabbit, Mintlify docs sync, and WAF security layers.
SPEC
echo "✅ Local gh-aw pipeline spec created."

# 4. Studio & High-Performance 8K Graphics/UI Environment Profile
mkdir -p ~/.flg_studio
cat << 'STUDIO' > ~/.flg_studio/graphics_profile.env
# FLG OS Studio High-Performance & High-Res Rendering Configuration
FLG_RENDER_MODE="ultra"
FLG_RESOLUTION_SCALE="8k_virtual"
FLG_GPU_ACCELERATION="enabled"
FLG_UI_FPS_CAP="120"
FLG_STUDIO_PIPELINE="optimized"
STUDIO
echo "✅ Studio 8K graphics performance profile written to ~/.flg_studio/graphics_profile.env"

echo "🎉 FLG Ultimate Local Upgrade Complete! (Zero GitHub push performed)."
