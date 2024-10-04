#!/bin/bash

apptainer exec -B /databases -B /software /software/containers/users/bcov/bcov_base_22-01-11.sif python ./ml_benchmarks/benchmarks/backbone_and_seq_design/common_scripts/ppi_score.py --af2_outputs oracle_outputs/*.pdb

