#!/usr/bin/env bash
# Parallel TIFF → PNG converter with a live progress bar
# Usage: ./convert_tiff_to_png.sh <DIRECTORY> [OUTPUT_DIR] [JOBS]
# 
# If OUTPUT_DIR is not provided, PNG files will be saved in the same directory as the TIFF files.
# JOBS can be set as environment variable or 3rd argument to control parallelism.

set -u
shopt -s nullglob

# Default parallelism: number of CPUs (override via 3rd arg or $JOBS)
JOBS_DEFAULT=$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
JOBS=${JOBS:-${3:-$JOBS_DEFAULT}}

BAR_LEN=${BAR_LEN:-50}

progress_bar() {
  local current=$1 total=$2
  local completed_char='#' empty_char='.'
  local perc=0 filled=0 i

  if (( total > 0 )); then
    perc=$(( current * 100 / total ))
    filled=$(( perc * BAR_LEN / 100 ))
  fi

  local bar='['
  for ((i=0; i<filled; i++)); do bar+="$completed_char"; done
  for ((i=filled; i<BAR_LEN; i++)); do bar+="$empty_char"; done
  bar+=']'
  printf "\r%s %d/%d (%d%%)" "$bar" "$current" "$total" "$perc"
}

convert_tiff_to_png() {
  local src=$1 dest=$2
  mkdir -p "$dest"
  tiff2png -destdir "$dest" "$src" >/dev/null 2>&1
}

cleanup() {
  printf "\nStopping, terminating running jobs...\n" >&2
  # Terminate any still-running background conversions
  while read -r pid; do kill "$pid" 2>/dev/null; done < <(jobs -pr)
}
trap cleanup INT TERM

SOURCE_DIR=${1:-}
DEST_DIR=${2:-$SOURCE_DIR}  # Default to same directory if not specified

if [[ -z ${SOURCE_DIR} ]]; then
  echo "Usage: $0 <directory> [output_dir] [jobs]" >&2
  echo "" >&2
  echo "Arguments:" >&2
  echo "  directory   - Directory containing .tif/.tiff files to convert" >&2
  echo "  output_dir  - (Optional) Directory to save PNG files (default: same as input)" >&2
  echo "  jobs        - (Optional) Number of parallel jobs (default: number of CPUs)" >&2
  exit 1
fi

if [[ ! -d $SOURCE_DIR ]]; then
  echo "Error: Directory does not exist: $SOURCE_DIR" >&2
  exit 1
fi

if ! command -v tiff2png >/dev/null 2>&1; then
  echo "Error: tiff2png not found. It should already be installed (comes with libtiff)." >&2
  echo "       If missing, install with: brew install libtiff" >&2
  exit 1
fi

# Collect files (supports both .tif and .tiff extensions, case-insensitive)
files=( "$SOURCE_DIR"/*.tif "$SOURCE_DIR"/*.tiff "$SOURCE_DIR"/*.TIF "$SOURCE_DIR"/*.TIFF )
len=${#files[@]}

if (( len == 0 )); then
  echo "No TIFF files found in $SOURCE_DIR" >&2
  exit 0
fi

# Create output directory if needed
mkdir -p "$DEST_DIR"

printf "Found %d TIFF file(s) in %s\n" "$len" "$SOURCE_DIR"
printf "Converting with %d parallel job(s)...\n" "$JOBS"
if [[ "$DEST_DIR" != "$SOURCE_DIR" ]]; then
  printf "Output directory: %s\n" "$DEST_DIR"
fi
printf "\n"

completed=0
failed=0
running=0

for file in "${files[@]}"; do
  convert_tiff_to_png "$file" "$DEST_DIR" &
  ((running++))

  # If we've hit the parallelism limit, wait for one job to finish
  if (( running >= JOBS )); then
    if wait -n; then
      :  # success
    else
      ((failed++))
    fi
    ((completed++))
    ((running--))
    progress_bar "$completed" "$len"
  fi
done

# Drain remaining jobs
while (( running > 0 )); do
  if wait -n; then
    :  # success
  else
    ((failed++))
  fi
  ((completed++))
  ((running--))
  progress_bar "$completed" "$len"
done

printf "\n\n"
if (( failed > 0 )); then
  echo "Done: $((len - failed)) succeeded, $failed failed."
  exit 1
else
  echo "✓ Conversion complete! Converted $len file(s) to PNG."
fi
