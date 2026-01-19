#!/bin/bash

# Usage: ./script.sh <directory> <extension>
directory="${1:-.}"  # Default to current directory if not provided
extension="$2"

if [ -z "$extension" ]; then
    echo "Usage: $0 <directory> <extension>"
    exit 1
fi

# Find all files with the given extension and cat their contents
find "$directory" -type f -name "*.$extension" -print0 | while IFS= read -r -d '' file; do
    echo "=== $file ==="
    cat "$file"
    echo ""
    echo "---"
    echo ""
done
