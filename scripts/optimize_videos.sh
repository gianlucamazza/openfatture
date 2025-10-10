#!/usr/bin/env bash
# Video Optimization Script for OpenFatture Media Assets
#
# Optimizes MP4 videos for web delivery with multiple quality tiers:
# - HD (1280x720): Primary web format, balanced quality/size
# - Low bandwidth (854x480): For slow connections
# - Mobile (640x360): For mobile devices
#
# Requirements: ffmpeg
#
# Usage:
#   ./scripts/optimize_videos.sh                    # Optimize all videos
#   ./scripts/optimize_videos.sh scenario_a_onboarding.mp4  # Optimize specific video

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly INPUT_DIR="media/output"
readonly VIDEO_DIR="media/videos"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "${SCRIPT_DIR}")"

# Video encoding settings (optimized for web delivery)
readonly HD_WIDTH=1280
readonly HD_HEIGHT=720
readonly HD_BITRATE="1500k"

readonly SD_WIDTH=854
readonly SD_HEIGHT=480
readonly SD_BITRATE="800k"

readonly MOBILE_WIDTH=640
readonly MOBILE_HEIGHT=360
readonly MOBILE_BITRATE="500k"

# Audio settings
readonly AUDIO_BITRATE="96k"
readonly AUDIO_SAMPLE_RATE=44100

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

# Get video information
get_video_info() {
    local input_file="$1"
    local duration size bitrate

    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${input_file}")
    size=$(du -h "${input_file}" | cut -f1)
    bitrate=$(ffprobe -v error -show_entries format=bit_rate -of default=noprint_wrappers=1:nokey=1 "${input_file}" | awk '{printf "%.0fk", $1/1000}')

    echo "Duration: ${duration}s | Size: ${size} | Bitrate: ${bitrate}"
}

# Optimize single video with quality tier
optimize_video() {
    local input_file="$1"
    local output_file="$2"
    local width="$3"
    local height="$4"
    local video_bitrate="$5"
    local tier_name="$6"

    log_info "Encoding ${tier_name}..."

    # Two-pass encoding for better quality
    # Pass 1: Analyze
    ffmpeg -y -i "${input_file}" \
        -c:v libx264 -preset slow -b:v "${video_bitrate}" \
        -vf "scale=${width}:${height}:flags=lanczos" \
        -pass 1 -an -f mp4 /dev/null \
        -loglevel error -stats

    # Pass 2: Encode
    ffmpeg -y -i "${input_file}" \
        -c:v libx264 -preset slow -b:v "${video_bitrate}" \
        -vf "scale=${width}:${height}:flags=lanczos" \
        -pass 2 \
        -c:a aac -b:a "${AUDIO_BITRATE}" -ar "${AUDIO_SAMPLE_RATE}" \
        -movflags +faststart \
        "${output_file}" \
        -loglevel error -stats

    # Cleanup pass files
    rm -f ffmpeg2pass-*.log

    local output_size
    output_size=$(du -h "${output_file}" | cut -f1)
    log_success "${tier_name}: ${output_size}"
}

# Process single video file
process_video() {
    local input_file="$1"
    local basename filename

    basename=$(basename "${input_file}" .mp4)
    filename="${basename}"

    log_info "Processing: ${filename}"
    log_info "$(get_video_info "${input_file}")"

    # Create output directory structure
    mkdir -p "${VIDEO_DIR}"/{hd,sd,mobile}

    # Generate optimized versions
    optimize_video "${input_file}" "${VIDEO_DIR}/hd/${filename}.mp4" \
        "${HD_WIDTH}" "${HD_HEIGHT}" "${HD_BITRATE}" "HD 720p"

    optimize_video "${input_file}" "${VIDEO_DIR}/sd/${filename}.mp4" \
        "${SD_WIDTH}" "${SD_HEIGHT}" "${SD_BITRATE}" "SD 480p"

    optimize_video "${input_file}" "${VIDEO_DIR}/mobile/${filename}.mp4" \
        "${MOBILE_WIDTH}" "${MOBILE_HEIGHT}" "${MOBILE_BITRATE}" "Mobile 360p"

    # Generate thumbnail (first frame)
    ffmpeg -y -i "${input_file}" -vframes 1 -q:v 2 \
        "${VIDEO_DIR}/${filename}_thumbnail.jpg" \
        -loglevel error

    log_success "Thumbnail: ${filename}_thumbnail.jpg"
    echo ""
}

# Main execution
main() {
    cd "${ROOT_DIR}"

    echo -e "${BLUE}🎬 OpenFatture Video Optimization${NC}"
    echo "=================================="
    echo ""

    check_dependencies || exit 1
    echo ""

    # Determine which videos to process
    local videos=()

    if [ $# -eq 0 ]; then
        # Process all videos in input directory
        log_info "Processing all videos in ${INPUT_DIR}/"
        while IFS= read -r -d '' file; do
            videos+=("$file")
        done < <(find "${INPUT_DIR}" -name "*.mp4" -print0)
    else
        # Process specified videos
        for arg in "$@"; do
            if [[ "$arg" == *.mp4 ]]; then
                videos+=("${INPUT_DIR}/${arg}")
            else
                videos+=("${INPUT_DIR}/${arg}.mp4")
            fi
        done
    fi

    if [ ${#videos[@]} -eq 0 ]; then
        log_error "No videos found to process"
        exit 1
    fi

    log_info "Found ${#videos[@]} video(s) to optimize"
    echo ""

    # Process each video
    for video in "${videos[@]}"; do
        if [ -f "${video}" ]; then
            process_video "${video}"
        else
            log_warning "File not found: ${video}"
        fi
    done

    # Summary
    echo -e "${GREEN}✅ Video optimization complete!${NC}"
    echo ""
    echo "Output structure:"
    tree "${VIDEO_DIR}" -L 2 -h || ls -lhR "${VIDEO_DIR}"
    echo ""
    echo "💡 Next steps:"
    echo "  - Review video quality in media/videos/"
    echo "  - Generate GIFs: ./scripts/generate_gifs.sh"
    echo "  - Update documentation with video links"
}

# Run main
main "$@"
