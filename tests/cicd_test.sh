#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$(realpath "$0")")
echo ${SCRIPT_DIR}

# Run the MONSDA command with the updated -c parameter
monsda -j 6 -c "${SCRIPT_DIR}/multitool.json" --directory "${SCRIPT_DIR}" --use-apptainer --apptainer-prefix "${SCRIPT_DIR}/Containers" --rerun-incomplete --rerun-triggers mtime