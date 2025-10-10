#!/usr/bin/env bash
# GIF Generation Script for OpenFatture Media Assets
#
# Converts MP4 videos to optimized GIF animations suitable for:
# - GitHub README embeds (< 5MB recommended)
# - Social media previews
# - Documentation inline demos
#
# Features:
# - High-quality palette generation for better colors
# - FPS optimization for smaller file size
# - Multiple duration options (full, 10s preview, 5s teaser)
#
# Requirements: ffmpeg
#
# Usage:
#   ./scripts/generate_gifs.sh                    # Convert all videos
#   ./scripts/generate_gifs.sh scenario_a_onboarding.mp4  # Convert specific video
#   ./scripts/generate_gifs.sh --preview scenario_b_invoice.mp4  # 10s preview only

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly INPUT_DIR="media/output"
readonly GIF_DIR="media/gifs"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "${SCRIPT_DIR}")"

# GIF encoding settings
readonly GIF_WIDTH=1280          # Width in pixels (maintain 16:9 aspect)
readonly GIF_FPS=15              # Frames per second (lower = smaller file)
readonly GIF_QUALITY=100         # Palette quality (0-256, higher = better)
readonly GIF_MAX_COLORS=128      # Max colors in palette (lower = smaller file)

# Duration presets
readonly PREVIEW_DURATION=10     # Preview clips (seconds)
readonly TEASER_DURATION=5       # Short teasers (seconds)

# File size targets
readonly MAX_SIZE_MB=5           # GitHub's comfortable embed size

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $*"
}

log_error() {
    echo -e "${RED}✗${NC}  $*" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $*" >&2
}

# Check dependencies
check_dependencies() {
    if ! command -v ffmpeg >/dev/null 2>&1; then
        log_error "ffmpeg not found. Install with: brew install ffmpeg"
        return 1
    fi
    log_success "ffmpeg found: $(ffmpeg -version | head -n1)"
}

# Get video duration
get_duration() {
    local input_file="$1"
    ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "${input_file}" | \
        awk '{printf "%.0f", $1}'
}

# Convert video to GIF with high quality
convert_to_gif() {
    local input_file="$1"
    local output_file="$2"
    local duration="${3:-}"  # Optional: clip duration
    local start_time="${4:-0}"  # Optional: start time

    local filters="fps=${GIF_FPS},scale=${GIF_WIDTH}:-1:flags=lanczos"
    local duration_args=""

    if [ -n "${duration}" ]; then
        duration_args="-ss ${start_time} -t ${duration}"
    fi

    # Generate optimized color palette
    local palette="/tmp/palette_$$.png"

    # shellcheck disable=SC2086
    ffmpeg -y ${duration_args} -i "${input_file}" \
        -vf "${filters},palettegen=max_colors=${GIF_MAX_COLORS}:stats_mode=diff" \
        "${palette}" \
        -loglevel error

    # Create GIF using palette
    # shellcheck disable=SC2086
    ffmpeg -y ${duration_args} -i "${input_file}" -i "${palette}" \
        -lavfi "${filters}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
        "${output_file}" \
        -loglevel error -stats

    # Cleanup palette
    rm -f "${palette}"

    # Report file size
    local size_kb size_mb
    size_kb=$(du -k "${output_file}" | cut -f1)
    size_mb=$(echo "scale=2; ${size_kb}/1024" | bc)

    if (( $(echo "${size_mb} > ${MAX_SIZE_MB}" | bc -l) )); then
        log_warning "Size: ${size_mb}MB (exceeds ${MAX_SIZE_MB}MB target)"
        log_info "Consider: reduce duration, FPS=${GIF_FPS}, or max_colors=${GIF_MAX_COLORS}"
    else
        log_success "Size: ${size_mb}MB"
    fi
}

# Process single video file
process_video() {
    local input_file="$1"
    local mode="${2:-all}"  # all, preview, teaser
    local basename filename duration

    basename=$(basename "${input_file}" .mp4)
    filename="${basename}"
    duration=$(get_duration "${input_file}")

    log_info "Processing: ${filename} (${duration}s)"

    # Create output directory
    mkdir -p "${GIF_DIR}"

    # Generate full GIF
    if [ "${mode}" == "all" ] || [ "${mode}" == "full" ]; then
        log_info "Creating full GIF..."
        convert_to_gif "${input_file}" "${GIF_DIR}/${filename}.gif"
    fi

    # Generate preview (first 10s)
    if [ "${mode}" == "all" ] || [ "${mode}" == "preview" ]; then
        if [ "${duration}" -gt "${PREVIEW_DURATION}" ]; then
            log_info "Creating ${PREVIEW_DURATION}s preview..."
            convert_to_gif "${input_file}" "${GIF_DIR}/${filename}_preview.gif" \
                "${PREVIEW_DURATION}" "0"
        else
            log_info "Skipping preview (video too short: ${duration}s)"
        fi
    fi

    # Generate teaser (first 5s)
    if [ "${mode}" == "all" ] || [ "${mode}" == "teaser" ]; then
        if [ "${duration}" -gt "${TEASER_DURATION}" ]; then
            log_info "Creating ${TEASER_DURATION}s teaser..."
            convert_to_gif "${input_file}" "${GIF_DIR}/${filename}_teaser.gif" \
                "${TEASER_DURATION}" "0"
        else
            log_info "Skipping teaser (video too short: ${duration}s)"
        fi
    fi

    echo ""
}

# Show usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [VIDEO_FILES...]

Convert MP4 videos to optimized GIF animations.

OPTIONS:
  --all         Generate full, preview, and teaser GIFs (default)
  --full        Generate full-length GIF only
  --preview     Generate 10s preview GIF only
  --teaser      Generate 5s teaser GIF only
  -h, --help    Show this help message

EXAMPLES:
  $0                                    # Convert all videos (all modes)
  $0 --preview scenario_a_onboarding.mp4  # 10s preview only
  $0 --teaser scenario_b_invoice.mp4 scenario_c_ai.mp4  # 5s teasers

SETTINGS:
  Resolution: ${GIF_WIDTH}px wide (16:9 aspect maintained)
  FPS: ${GIF_FPS}
  Max Colors: ${GIF_MAX_COLORS}
  Target Size: < ${MAX_SIZE_MB}MB (for GitHub embeds)
EOF
}

# Parse arguments
parse_args() {
    local mode="all"
    local videos=()

    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                mode="all"
                shift
                ;;
            --full)
                mode="full"
                shift
                ;;
            --preview)
                mode="preview"
                shift
                ;;
            --teaser)
                mode="teaser"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                videos+=("$1")
                shift
                ;;
        esac
    done

    echo "${mode}"
    printf '%s\n' "${videos[@]}"
}

# Main execution
main() {
    cd "${ROOT_DIR}"

    echo -e "${BLUE}🎞️  OpenFatture GIF Generation${NC}"
    echo "=============================="
    echo ""

    check_dependencies || exit 1
    echo ""

    # Parse arguments
    local mode videos=()
    while IFS= read -r line; do
        if [ -z "${mode:-}" ]; then
            mode="$line"
        else
            videos+=("$line")
        fi
    done < <(parse_args "$@")

    # Determine which videos to process
    if [ ${#videos[@]} -eq 0 ]; then
        # Process all videos in input directory
        log_info "Processing all videos in ${INPUT_DIR}/"
        while IFS= read -r -d '' file; do
            videos+=("$file")
        done < <(find "${INPUT_DIR}" -name "*.mp4" -print0)
    else
        # Resolve video paths
        local resolved_videos=()
        for video in "${videos[@]}"; do
            if [[ "$video" == *.mp4 ]]; then
                resolved_videos+=("${INPUT_DIR}/${video}")
            else
                resolved_videos+=("${INPUT_DIR}/${video}.mp4")
            fi
        done
        videos=("${resolved_videos[@]}")
    fi

    if [ ${#videos[@]} -eq 0 ]; then
        log_error "No videos found to process"
        exit 1
    fi

    log_info "Found ${#videos[@]} video(s) to convert (mode: ${mode})"
    echo ""

    # Process each video
    for video in "${videos[@]}"; do
        if [ -f "${video}" ]; then
            process_video "${video}" "${mode}"
        else
            log_warning "File not found: ${video}"
        fi
    done

    # Summary
    echo -e "${GREEN}✅ GIF generation complete!${NC}"
    echo ""
    echo "Output files:"
    ls -lh "${GIF_DIR}"/*.gif 2>/dev/null || echo "No GIFs generated"
    echo ""
    echo "💡 Next steps:"
    echo "  - Review GIF quality in media/gifs/"
    echo "  - Embed in README.md with: ![Demo](media/gifs/scenario_a_onboarding.gif)"
    echo "  - For large files, consider hosting on GitHub Releases or external CDN"
}

# Run main
main "$@"
