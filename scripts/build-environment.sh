#!/bin/bash

# Set the directory containing the Soong UI tests and XML files
SOONG_UI_DIR="$BUILD_TOP/build/soong"

# Add the Soong directory to the PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$SOONG_UI_DIR"

# Loop through each subdirectory in the SOONG_UI_DIR and add it to PYTHONPATH
for dir in "$SOONG_UI_DIR"/*; do
    if [ -d "$dir" ]; then
        export PYTHONPATH="$PYTHONPATH:$dir"
    fi
done

# End of script
