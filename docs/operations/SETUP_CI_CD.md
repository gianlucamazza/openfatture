# CI/CD Setup Instructions

## ✅ Completed

The following has been set up automatically:

- ✓ Git LFS configuration (`.gitattributes`, `.gitignore`)
- ✓ GitHub Actions workflows:
  - `media-generation.yml` - Automated video generation with Anthropic Claude
  - `media-validation.yml` - PR validation for media files
  - `media-optimization.yml` - Post-processing (HD/SD/Mobile/GIF)
- ✓ Documentation (`docs/CI_CD_MEDIA_AUTOMATION.md`)
- ✓ Makefile target (`make media-ci`)
- ✓ Environment example (`.env.demo`)
- ✓ README badge

## 🔧 Manual Steps Required

### 1. Configure GitHub Secret

The workflows require an Anthropic API key to be configured as a GitHub secret.

**Steps:**

```bash
# Option A: Using GitHub CLI
gh secret set ANTHROPIC_API_KEY

# You'll be prompted to paste your key
# Use your Anthropic API key: sk-ant-api03-...

# Option B: Using GitHub Web UI
# 1. Go to: https://github.com/YOUR_USERNAME/openfatture/settings/secrets/actions
# 2. Click "New repository secret"
# 3. Name: ANTHROPIC_API_KEY
# 4. Value: [Your Anthropic API key here]
# 5. Click "Add secret"
```

### 2. (Optional) Configure Environment Protection

For production safety, add manual approval requirements:

```bash
# 1. Go to: Settings → Environments
# 2. Create environment: "media-automation"
# 3. Enable "Required reviewers"
# 4. Add 1-2 reviewers
```

### 3. Test Locally (Optional)

Before pushing to GitHub, test the CI workflow locally:

```bash
# Create .env with Anthropic configuration
cat > .env <<EOF
DATABASE_URL=sqlite:///./openfatture_demo.db
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-5
OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-api03-XcW-Acu1MA...
EOF

# Test CI simulation
make media-ci

# This will:
# 1. Check prerequisites (VHS, ffmpeg, uv)
# 2. Verify Anthropic configuration
# 3. Reset demo environment
# 4. Generate all scenario videos
# 5. Show summary and next steps
```

### 4. Push Changes to GitHub

Once you've configured the secret, commit and push:

```bash
# Add all workflow files
git add .github/workflows/media-*.yml
git add docs/CI_CD_MEDIA_AUTOMATION.md
git add makefiles/media.mk
git add .env.demo
git add .gitattributes .gitignore
git add README.md

# Commit
git commit -m "feat(ci): add CI/CD media automation with Anthropic Claude

- Add media-generation.yml workflow (nightly + manual)
- Add media-validation.yml workflow (PR checks)
- Add media-optimization.yml workflow (HD/SD/Mobile/GIF)
- Add comprehensive CI/CD documentation
- Add make media-ci target for local testing
- Configure Anthropic Claude Sonnet 4.5
- Fix Git LFS configuration

Cost: ~$1.50/month for nightly runs with prompt caching

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### 5. Trigger First Workflow

Test the workflow manually before waiting for the nightly schedule:

```bash
# Option A: Using GitHub CLI
gh workflow run media-generation.yml \
  --ref main \
  -f scenario=A \
  -f skip_optimization=false

# Option B: Using GitHub Web UI
# 1. Go to: Actions → Media Generation
# 2. Click "Run workflow"
# 3. Select: scenario=A, skip_optimization=false
# 4. Click "Run workflow"
# 5. Wait ~5-10 minutes
# 6. Download artifacts from the run page
```

## 📊 Monitoring

### Check Workflow Status

```bash
# List recent runs
gh run list --workflow=media-generation.yml --limit 5

# View specific run
gh run view <RUN_ID> --log

# Download artifacts
gh run download <RUN_ID>
```

### Monitor Costs

- **Anthropic Console**: https://console.anthropic.com/settings/usage
- **Estimated Cost**: ~$0.036 per run (~$1.50/month for nightly runs)

### View Workflow Badges

Check README.md for workflow status badges:
- [![Media Generation](https://github.com/YOUR_USERNAME/openfatture/actions/workflows/media-generation.yml/badge.svg)](https://github.com/YOUR_USERNAME/openfatture/actions/workflows/media-generation.yml)

## 📚 Documentation

For detailed information, see:
- **CI/CD Guide**: [`docs/CI_CD_MEDIA_AUTOMATION.md`](docs/CI_CD_MEDIA_AUTOMATION.md)
- **Media Automation**: [`media/automation/README.md`](media/automation/README.md)
- **Workflows**: [`.github/workflows/`](.github/workflows/)

## 🐛 Troubleshooting

### Workflow fails with "ANTHROPIC_API_KEY not set"
→ Make sure you added the secret in step 1

### Videos not generated
→ Check workflow logs: `gh run view <RUN_ID> --log`

### High costs
→ Review `docs/CI_CD_MEDIA_AUTOMATION.md` for cost optimization tips

### Local testing fails
→ Run `make media-check` to verify prerequisites

## 🎉 What's Next

After completing these steps:

1. **Monitor first run**: Watch the workflow complete successfully
2. **Review artifacts**: Download and check generated videos
3. **Adjust schedule**: Modify cron schedule in `media-generation.yml` if needed
4. **Add scenarios**: Create new `.tape` files in `media/automation/`
5. **Optimize costs**: Enable prompt caching (already configured)

---

**Questions?** See [`docs/CI_CD_MEDIA_AUTOMATION.md`](docs/CI_CD_MEDIA_AUTOMATION.md) for comprehensive documentation.
