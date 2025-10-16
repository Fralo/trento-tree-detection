#!/usr/bin/env bash
# Parallel TIFF → PNG converter with a live progress bar
# Usage: ./convert.sh <SOURCE_DIR> <DEST_DIR> [JOBS]
# Or:    JOBS=8 ./convert.sh <SOURCE_DIR> <DEST_DIR>

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
DEST_DIR=${2:-}

if [[ -z ${SOURCE_DIR} || -z ${DEST_DIR} ]]; then
  echo "Usage: $0 <source_dir> <dest_dir> [jobs]" >&2
  exit 1
fi
if [[ ! -d $SOURCE_DIR ]]; then
  echo "Source directory does not exist: $SOURCE_DIR" >&2
  exit 1
fi
if ! command -v tiff2png >/dev/null 2>&1; then
  echo "tiff2png not found. Install it (e.g. 'brew install libtiff')." >&2
  exit 1
fi

# Collect files (top-level of SOURCE_DIR). Add/keep uppercase variants.
files=( "$SOURCE_DIR"/*.tif "$SOURCE_DIR"/*.tiff "$SOURCE_DIR"/*.TIF "$SOURCE_DIR"/*.TIFF )
len=${#files[@]}
if (( len == 0 )); then
  echo "No TIFF files found in $SOURCE_DIR." >&2
  exit 0
fi

printf "Converting %d files with %d parallel jobs...\n" "$len" "$JOBS"

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

printf "\n"
if (( failed > 0 )); then
  echo "Done: $((len - failed)) succeeded, $failed failed."
else
  echo "Conversion complete! Converted $len files."
fi
