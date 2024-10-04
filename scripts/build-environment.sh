#!/bin/bash

# Check if BUILD_TOP is set
if [ -z "$BUILD_TOP" ]; then
    echo "Error: BUILD_TOP is not set."
    exit 1
fi

# Set the directories containing the Soong UI tests and XML files
SOONG_UI_DIR="$BUILD_TOP/build/soong"
BLUEPRINT_DIR="$BUILD_TOP/build/blueprint"

# Initialize a variable to collect all directories
PYTHONPATH_DIRS="$SOONG_UI_DIR"

# Function to recursively add directories to PYTHONPATH_DIRS
add_to_pythonpath() {
  for dir in "$1"/*; do
    if [ -d "$dir" ]; then
      PYTHONPATH_DIRS="$PYTHONPATH_DIRS:$dir"
      add_to_pythonpath "$dir"  # Recursive call for subdirectories
    fi
  done
}

# Add Soong UI directories recursively
add_to_pythonpath "$SOONG_UI_DIR"

# Add Blueprint directories recursively
add_to_pythonpath "$BLUEPRINT_DIR"

# Set PYTHONPATH, adding to existing PYTHONPATH if set
if [ -n "$PYTHONPATH" ]; then
    export PYTHONPATH="$PYTHONPATH:$PYTHONPATH_DIRS"
else
    export PYTHONPATH="$PYTHONPATH_DIRS"
fi

# End of script