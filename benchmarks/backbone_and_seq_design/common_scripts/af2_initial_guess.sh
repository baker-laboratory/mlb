#!/bin/bash

mkdir oracle_outputs 2>/dev/null

mkdir af2_temp 2>/dev/null
mkdir af2_temp/splits 2>/dev/null

SILENT_TOOLS=/software/lab/silent_tools/

$SILENT_TOOLS/silentfrompdbs threaded_designs/*.pdb > af2_temp/threaded_designs.silent

cd af2_temp/splits
/software/lab/silent_tools/silentsplittargetlength ../threaded_designs.silent 500
cd ..

apptainer=/software/containers/users/bcov/bcov_af2.sif
af2_script=/software/lab/ppi/bcov_scripts/bcov_nate_af2_early_stop/interfaceAF2predict_bcov.py


for silent_file in splits/*.silent; do
    apptainer exec --nv $apptainer python $af2_script -silent $silent_file
done

$SILENT_TOOLS/silentls out.silent | sed 's/_af2pred/_oracle/g' | $SILENT_TOOLS/silentrename out.silent > renamed.silent
$SILENT_TOOLS/silentscorefile renamed.silent

cd ../oracle_outputs
$SILENT_TOOLS/silentextract ../af2_temp/renamed.silent
cp ../af2_temp/renamed.sc af2_scores.sc




