#!/bin/bash

IFS=$'\n'
for line in $(cat inputs.txt); do
    echo ./generate_threaded_design.sh $line | bash
done
unset IFS
./scripts/generate_oracle_outputs_from_threaded_designs.sh
./scripts/score.sh

