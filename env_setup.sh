#!/bin/bash

# Navigate to the directory containing the YAML files
cd "$(dirname "$0")/conda_envs"

# Loop through all .yml files and create conda environments
for env_file in *.yml; do
    echo "Creating conda environment from $env_file..."
    conda env create -f "$env_file"
    echo "Finished creating environment from $env_file"
done
