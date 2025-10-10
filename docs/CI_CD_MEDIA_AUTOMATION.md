# CI/CD Media Automation

Automated media generation and optimization pipeline for OpenFatture using GitHub Actions and Anthropic Claude.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Workflows](#workflows)
- [Usage](#usage)
- [Cost Management](#cost-management)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Overview

The CI/CD media automation pipeline generates demonstration videos, GIFs, and thumbnails automatically using:

- **VHS**: Terminal recording from `.tape` scripts
- **Anthropic Claude Sonnet 4.5**: AI-powered CLI interactions
- **FFmpeg**: Video optimization and format conversion
- **GitHub Actions**: Orchestration and scheduling

### Key Features

- **Automated Generation**: Nightly video generation at 2 AM UTC
- **Manual Triggers**: On-demand generation for specific scenarios
- **Quality Validation**: Automatic linting and validation on PRs
- **Multi-Format**: HD (720p), SD (480p), Mobile (360p), GIF previews
- **Cost Efficient**: ~$1.50/month for 30 runs with prompt caching
- **Artifact Storage**: 7-30 day retention for generated media

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Media Automation Pipeline                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Pull Request    │
│  (*.tape, *.sh)  │
└────────┬─────────┘
         │
         v
┌────────────────────────────────┐
│  media-validation.yml          │
│  ├─ Lint tape files            │
│  ├─ Validate shell scripts     │
│  ├─ Check for API keys         │
│  └─ Post PR comment            │
└────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐
│  Schedule        │       │  Manual Trigger  │
│  (Daily 2 AM)    │       │  (workflow_dispatch)
└────────┬─────────┘       └────────┬─────────┘
         │                          │
         └──────────┬───────────────┘
                    v
┌─────────────────────────────────────────────┐
│  media-generation.yml                       │
│  ├─ Setup: VHS, ffmpeg, uv, Python          │
│  ├─ Configure: Anthropic Claude Sonnet 4.5  │
│  ├─ Reset: Demo environment & database      │
│  ├─ Generate: Run VHS tape scenarios        │
│  ├─ Upload: Artifacts (7 days)              │
│  └─ Trigger: Optimization workflow          │
└────────────────────┬────────────────────────┘
                     │
                     v (repository_dispatch)
┌─────────────────────────────────────────────┐
│  media-optimization.yml                     │
│  ├─ Download: Videos from generation run    │
│  ├─ Optimize: HD/SD/Mobile versions         │
│  ├─ Generate: GIF previews (10s)            │
│  ├─ Generate: Thumbnails (640px)            │
│  ├─ Upload: Optimized artifacts (30 days)   │
│  └─ Summary: Size comparison report         │
└─────────────────────────────────────────────┘
```

## Setup

### Prerequisites

- GitHub repository with Actions enabled
- Anthropic API key (Claude access)
- Git LFS installed and configured
- Repository secrets configured

### 1. Configure GitHub Secrets

#### Required Secrets

Navigate to: `Repository Settings → Secrets and variables → Actions`

| Secret Name | Value | Usage |
|------------|-------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Anthropic Claude API authentication |

**Steps:**
```bash
# 1. Go to GitHub repository
https://github.com/YOUR_USERNAME/openfatture/settings/secrets/actions

# 2. Click "New repository secret"

# 3. Add secret:
Name:  ANTHROPIC_API_KEY
Value: sk-ant-api03-...  # Your Anthropic API key

# 4. Click "Add secret"
```

### 2. Configure Environment Protection (Optional)

For production environments, add manual approval requirements:

```bash
# 1. Go to Settings → Environments
https://github.com/YOUR_USERNAME/openfatture/settings/environments

# 2. Create "media-automation" environment

# 3. Enable "Required reviewers"
   - Add 1-2 team members for approval

# 4. Add environment secrets (optional)
   - Can override ANTHROPIC_API_KEY per environment
```

### 3. Verify Git LFS

```bash
# Check Git LFS is installed
git lfs version
# Output: git-lfs/3.7.0 (GitHub; darwin arm64; go 1.22.5)

# Verify video files are tracked
git lfs ls-files
# Output:
# 8c128a89d4 * media/output/scenario_a_onboarding.mp4
# 11637cf7ad * media/output/scenario_b_invoice_creation.mp4
# ...
```

### 4. Local Development Setup

```bash
# Install VHS (for local testing)
brew install vhs  # macOS
# or
curl -fsSL https://github.com/charmbracelet/vhs/releases/download/v0.10.0/vhs_Linux_x86_64.tar.gz | tar -xz

# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Ubuntu

# Configure Anthropic locally
cp .env.demo .env
# Edit .env and set:
# AI_PROVIDER=anthropic
# AI_MODEL=claude-sonnet-4-5
# OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...
```

## Workflows

### media-generation.yml

**Purpose**: Generate demonstration videos using VHS and Anthropic AI

**Triggers**:
- Schedule: Daily at 2 AM UTC (`cron: '0 2 * * *'`)
- Manual: Via workflow dispatch

**Configuration**:
```yaml
Timeout: 45 minutes
Runner: ubuntu-latest
Environment: media-automation (optional)
Artifacts: 7 days retention
Cost per run: ~$0.036 (with prompt caching)
```

**Steps**:
1. Checkout repository with Git LFS
2. Install VHS, ffmpeg, uv, Python dependencies
3. Configure Anthropic Claude Sonnet 4.5 from secrets
4. Reset demo environment (database, sample data)
5. Generate videos (all scenarios or specific one)
6. Upload videos as artifacts
7. Trigger optimization workflow

**Key Environment Variables**:
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-5
OPENFATTURE_AI_ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
AI_CHAT_ENABLED=true
AI_TOOLS_ENABLED=true
```

### media-validation.yml

**Purpose**: Validate tape files and scripts on pull requests

**Triggers**:
- Pull requests affecting:
  - `media/automation/**/*.tape`
  - `scripts/reset_demo.sh`
  - `scripts/check_ollama.sh`
  - `scripts/optimize_videos.sh`
  - `scripts/generate_gifs.sh`
  - `.github/workflows/media-*.yml`

**Validation Checks**:
- ✓ Tape file syntax (Output, Set Shell, Set Theme directives)
- ✓ Shell script syntax (`bash -n`)
- ✓ No hardcoded API keys
- ✓ No absolute file paths
- ✓ Supported themes only (e.g., not "Solarized Dark")
- ✓ Sleep commands have time units (ms/s)

**Outputs**:
- PR comment with validation results
- Pass/fail status for merge protection

### media-optimization.yml

**Purpose**: Post-process videos into multiple formats and previews

**Triggers**:
- Repository dispatch from media-generation.yml
- Manual: Via workflow dispatch with source run ID

**Processing**:
```bash
# Video Optimization
HD (720p):     High quality for web embedding
SD (480p):     Balanced quality/size for documentation
Mobile (360p): Lightweight for mobile devices

# GIF Generation
Duration: 10 seconds preview
Frame rate: 10 fps
Palette: Optimized per video

# Thumbnails
Resolution: 640px width (aspect preserved)
Frame: 1 second into video
Format: JPEG
```

**Artifacts**:
- `media-optimized-videos-*`: HD/SD/Mobile MP4 files (30 days)
- `media-gifs-*`: GIF previews (30 days)
- `media-thumbnails-*`: JPEG thumbnails (30 days)

## Usage

### Manual Video Generation

#### Generate All Scenarios
```bash
# Via GitHub Actions UI
1. Go to Actions → Media Generation
2. Click "Run workflow"
3. Select branch: main
4. Scenario: all
5. Skip optimization: false (unchecked)
6. Click "Run workflow"

# Via GitHub CLI
gh workflow run media-generation.yml \
  --ref main \
  -f scenario=all \
  -f skip_optimization=false
```

#### Generate Specific Scenario
```bash
# Via GitHub CLI
gh workflow run media-generation.yml \
  --ref main \
  -f scenario=A \
  -f skip_optimization=false

# Available scenarios: A, B, C, D, E
# A: Onboarding and setup
# B: Invoice creation workflow
# C: AI assistant interaction
# D: Batch operations
# E: Dashboard and analytics
```

### Manual Optimization

If you have videos from a previous run:

```bash
# Get the source run ID
gh run list --workflow=media-generation.yml --limit 5

# Trigger optimization
gh workflow run media-optimization.yml \
  --ref main \
  -f source_run_id=1234567890 \
  -f generate_gifs=true \
  -f generate_thumbnails=true
```

### Download Artifacts

```bash
# List recent runs
gh run list --workflow=media-generation.yml

# Download artifacts from specific run
gh run download 1234567890

# This creates directories:
# media-videos-123/
# media-optimized-videos-124/
# media-gifs-124/
# media-thumbnails-124/
```

### Local Testing

```bash
# Test a single scenario locally
make media-scenarioA

# Test all scenarios
make media-all

# Check prerequisites
make media-check

# Reset demo environment
./scripts/reset_demo.sh
```

## Cost Management

### Anthropic API Pricing (October 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cached Read (per 1M tokens) |
|-------|----------------------|------------------------|------------------------------|
| Claude Sonnet 4.5 | $3.00 | $15.00 | $0.30 (90% discount) |

### Cost Estimates

**Per Run**:
```
Scenario input tokens:  ~2,000 (scenario C example)
Scenario output tokens: ~500

Cost per scenario:
= (2000 × $3 / 1,000,000) + (500 × $15 / 1,000,000)
= $0.006 + $0.0075
= $0.0135 per scenario

Full run (5 scenarios): ~$0.036
With prompt caching: ~$0.012 (67% savings)
```

**Monthly (Nightly Runs)**:
```
30 runs × $0.012 = ~$0.36/month (with caching)
30 runs × $0.036 = ~$1.08/month (without caching)
```

**Annual**:
```
365 runs × $0.012 = ~$4.38/year (with caching)
```

### Cost Optimization Tips

1. **Enable Prompt Caching**:
   - Already enabled in `openfatture/ai/providers/anthropic.py`
   - Saves 90% on repeated system prompts
   - Especially effective for similar scenarios

2. **Reduce Generation Frequency**:
   ```yaml
   # Change from daily to weekly
   schedule:
     - cron: '0 2 * * 0'  # Sunday 2 AM UTC
   ```

3. **Generate Specific Scenarios**:
   ```bash
   # Only generate changed scenarios
   gh workflow run media-generation.yml -f scenario=C
   ```

4. **Monitor Usage**:
   ```bash
   # Check Anthropic Console
   https://console.anthropic.com/settings/usage

   # Set up billing alerts
   # Settings → Billing → Usage notifications
   ```

5. **Use Lower-Cost Models for Testing**:
   ```bash
   # In .env for local testing
   AI_MODEL=claude-3-5-haiku  # $0.80/M input, $4/M output
   ```

### Budget Alerts

Set up GitHub Actions spending limits:

```bash
# Repository Settings → Billing → Spending limits
1. Set monthly spending limit: $10
2. Enable email notifications at 75%, 90%, 100%
3. Monitor Actions minutes usage
```

## Troubleshooting

### Common Issues

#### 1. Workflow Fails: "ANTHROPIC_API_KEY not set"

**Symptom**:
```
Error: AI provider anthropic is not configured
Required: OPENFATTURE_AI_ANTHROPIC_API_KEY
```

**Solution**:
```bash
# Verify secret exists
gh secret list | grep ANTHROPIC

# Add secret if missing
gh secret set ANTHROPIC_API_KEY

# Or via UI:
Repository Settings → Secrets → Actions → New secret
```

#### 2. VHS Recording Hangs

**Symptom**:
```
Timeout after 45 minutes
VHS process stuck on "Type" command
```

**Solution**:
- Check tape file for infinite loops
- Verify `Sleep` commands have reasonable durations
- Add `Ctrl+C` before exit if process hangs
- Test locally first: `vhs media/automation/scenario_a.tape`

#### 3. Video Quality Issues

**Symptom**:
```
Generated video is blurry or has artifacts
```

**Solution**:
```bash
# In tape file, adjust settings:
Set Width 1920
Set Height 1080
Set FontSize 16
Set LineHeight 1.4

# Check theme is supported
Set Theme "Dracula"  # NOT "Solarized Dark"
```

#### 4. Git LFS Errors

**Symptom**:
```
Error: Cannot pull LFS files
Pointer file instead of actual video
```

**Solution**:
```bash
# Verify LFS is installed in workflow
- name: Setup Git LFS
  run: |
    git lfs install
    git lfs pull

# Check .gitattributes
*.mp4 filter=lfs diff=lfs merge=lfs -text
```

#### 5. Optimization Workflow Not Triggered

**Symptom**:
```
Generation completes but optimization doesn't start
```

**Solution**:
```bash
# Check repository_dispatch trigger
- name: Trigger optimization workflow
  uses: peter-evans/repository-dispatch@v3
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    event-type: media-optimization-trigger

# Manually trigger if needed
gh workflow run media-optimization.yml -f source_run_id=<RUN_ID>
```

#### 6. High Costs / Token Usage

**Symptom**:
```
Anthropic bill higher than expected
```

**Solution**:
```bash
# 1. Verify prompt caching is enabled
# openfatture/ai/providers/anthropic.py
extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}

# 2. Check token usage in logs
grep "token_usage" workflow_logs.txt

# 3. Reduce max_tokens if needed
AI_MAX_TOKENS=1000  # Instead of 2000

# 4. Use cheaper model for testing
AI_MODEL=claude-3-5-haiku
```

### Debug Workflows Locally

Install and use `act` to test workflows locally:

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Create secrets file
cat > .secrets <<EOF
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Run workflow locally
act workflow_dispatch \
  --workflows .github/workflows/media-generation.yml \
  --secret-file .secrets \
  --input scenario=A

# Run specific job
act --job generate \
  --workflows .github/workflows/media-generation.yml \
  --secret-file .secrets
```

### Logs and Debugging

```bash
# View recent workflow runs
gh run list --workflow=media-generation.yml --limit 10

# View specific run logs
gh run view 1234567890 --log

# Download logs
gh run view 1234567890 --log > debug.log

# Search for errors
grep -i "error\|failed" debug.log

# Check AI responses
grep "AI response" debug.log
```

## Maintenance

### Weekly Tasks

- [ ] Review workflow run success rate
- [ ] Check artifact storage usage
- [ ] Verify generated videos quality
- [ ] Monitor API costs in Anthropic Console

```bash
# Weekly check script
gh run list --workflow=media-generation.yml --limit 7 --json status,conclusion
```

### Monthly Tasks

- [ ] Update VHS to latest version
- [ ] Review and optimize tape files
- [ ] Clean up old artifacts (auto-expires after 7-30 days)
- [ ] Review Anthropic usage and costs
- [ ] Update dependencies (`uv lock --upgrade`)

```bash
# Monthly maintenance
./scripts/maintenance_monthly.sh  # TODO: Create this script

# Update dependencies
uv lock --upgrade
uv sync --all-extras
```

### Quarterly Tasks

- [ ] Evaluate AI model options (Anthropic releases)
- [ ] Review and update scenarios
- [ ] Optimize workflow performance
- [ ] Update documentation
- [ ] Security audit (API keys, secrets)

### Version Updates

**Anthropic Models**:
```bash
# Check for new models
# https://docs.anthropic.com/claude/docs/models-overview

# Update in:
# 1. openfatture/ai/config/settings.py
# 2. .github/workflows/media-generation.yml
# 3. .env.demo
# 4. docs/CI_CD_MEDIA_AUTOMATION.md
```

**VHS Updates**:
```bash
# Check latest version
# https://github.com/charmbracelet/vhs/releases

# Update in workflow:
- name: Install VHS
  run: |
    curl -fsSL https://github.com/charmbracelet/vhs/releases/download/v0.11.0/vhs_Linux_x86_64.tar.gz | tar -xz
```

**Dependency Updates**:
```bash
# Update all dependencies
uv lock --upgrade

# Update specific dependency
uv lock --upgrade-package anthropic

# Commit changes
git add uv.lock
git commit -m "chore: update dependencies"
```

### Backup and Recovery

**Backup Media Artifacts**:
```bash
# Download all recent artifacts
gh run list --workflow=media-generation.yml --limit 30 --json databaseId -q '.[].databaseId' | \
  xargs -I {} gh run download {}

# Upload to external storage (optional)
rclone copy media-videos-*/ s3:backup/openfatture/media/
```

**Backup Workflow Configurations**:
```bash
# Already in Git, but create snapshots
tar -czf workflows-backup-$(date +%Y%m%d).tar.gz .github/workflows/media-*.yml

# Store in safe location
cp workflows-backup-*.tar.gz ~/backups/
```

### Monitoring and Alerts

**GitHub Actions Monitoring**:
```yaml
# Add to .github/workflows/monitoring.yml (optional)
name: Workflow Monitoring
on:
  schedule:
    - cron: '0 8 * * 1'  # Monday 8 AM UTC

jobs:
  check-failures:
    runs-on: ubuntu-latest
    steps:
      - name: Check for failed runs
        run: |
          failed=$(gh run list --workflow=media-generation.yml --limit 7 --json status,conclusion -q '[.[] | select(.conclusion == "failure")] | length')
          if [ "$failed" -gt 2 ]; then
            echo "Warning: $failed failures in last 7 runs"
            # Send notification
          fi
```

**Cost Alerts**:
- Set up Anthropic Console billing alerts
- Monitor GitHub Actions minutes (2000 free/month)
- Review monthly in Anthropic dashboard

### Support and Resources

- **OpenFatture Docs**: `/docs/MEDIA_AUTOMATION.md`
- **VHS Documentation**: https://github.com/charmbracelet/vhs
- **Anthropic Docs**: https://docs.anthropic.com/claude/docs
- **GitHub Actions**: https://docs.github.com/en/actions
- **FFmpeg Guide**: https://ffmpeg.org/documentation.html

---

**Last Updated**: 2025-10-10
**Version**: 1.0.0
**Maintained By**: OpenFatture Team
