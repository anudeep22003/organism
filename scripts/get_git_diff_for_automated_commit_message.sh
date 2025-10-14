#!/usr/bin/env bash

# Output file - TEMPORARY file first to avoid recursion issues
TEMP_OUTPUT_FILE=$(mktemp)
FINAL_OUTPUT_FILE="commit_details.txt"

# Directories/patterns to explicitly exclude
EXCLUDE_DIRS=(
  "node_modules" 
  ".venv"
  ".mypy_cache"
  "__pycache__"
  ".pytest_cache"
  ".ruff_cache"
  "backend/lib"
)

# File extensions to exclude
EXCLUDE_EXTS=(
  "lock" # package lock files
  "pyc"
  "pyo"
  "so"
  "jpg" "jpeg" "png" "gif" "svg" "ico" # images
  "pdf" "zip" "tar" "gz" "xz" "bz2" "rar" "exe" "bin" "dat" # binaries
)

# Start with a clean output file
echo "### DIFF ###" > "$TEMP_OUTPUT_FILE"

# Get a concise diff with stats first
git diff --cached --stat >> "$TEMP_OUTPUT_FILE"

# Add the full diff
echo -e "\n### FULL DIFF ###" >> "$TEMP_OUTPUT_FILE"
git diff --cached >> "$TEMP_OUTPUT_FILE"

echo -e "\n### FILE CONTENTS (SELECTED) ###\n" >> "$TEMP_OUTPUT_FILE"

# Get all staged files - but EXCLUDE commit_details.txt even if it's staged
for file in $(git diff --cached --name-only | grep -v "commit_details.txt"); do
  # Check if file is in excluded directories
  skip=0
  for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
    if [[ "$file" == *"$exclude_dir"* ]]; then
      echo "### $file (In excluded directory $exclude_dir, skipping) ###" >> "$TEMP_OUTPUT_FILE"
      skip=1
      break
    fi
  done
  
  # Skip if in excluded directory
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  # Check if file has excluded extension
  file_ext="${file##*.}"
  for exclude_ext in "${EXCLUDE_EXTS[@]}"; do
    if [ "$file_ext" = "$exclude_ext" ]; then
      echo "### $file (Excluded extension .$file_ext, skipping) ###" >> "$TEMP_OUTPUT_FILE"
      skip=1
      break
    fi
  done
  
  # Skip if has excluded extension
  if [ $skip -eq 1 ]; then
    continue
  fi
  
  echo "### $file ###" >> "$TEMP_OUTPUT_FILE"
  if [ -f "$file" ]; then
    # Get file size before writing it
    file_size=$(du -k "$file" | cut -f1)
    
    # Skip large files (>50KB)
    if [ "$file_size" -gt 50 ]; then
      echo "File too large to include (${file_size}KB)" >> "$TEMP_OUTPUT_FILE"
    else
      # Check if file is binary (more reliable than extension check)
      if file "$file" | grep -q "binary"; then
        echo "Binary file, skipping content" >> "$TEMP_OUTPUT_FILE"
      else
        cat "$file" >> "$TEMP_OUTPUT_FILE"
      fi
    fi
  else
    echo "File deleted" >> "$TEMP_OUTPUT_FILE"
  fi
  echo -e "\n" >> "$TEMP_OUTPUT_FILE"
done

# Copy from temp file to final output, then remove temp file
cp "$TEMP_OUTPUT_FILE" "$FINAL_OUTPUT_FILE"
rm "$TEMP_OUTPUT_FILE"

# Unstage commit_details.txt if it was previously staged
if git ls-files --stage | grep -q "commit_details.txt"; then
  git restore --staged "$FINAL_OUTPUT_FILE" 2>/dev/null
fi

# Output file size information
SIZE=$(du -h "$FINAL_OUTPUT_FILE" | cut -f1)
LINES=$(wc -l < "$FINAL_OUTPUT_FILE")

echo "Commit details written to $FINAL_OUTPUT_FILE ($SIZE, $LINES lines)"
