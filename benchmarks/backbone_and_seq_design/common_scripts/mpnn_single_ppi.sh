#!/bin/bash

pdb=$1
n_outputs=$2

name=$(basename $pdb .pdb)

run_dir=mpnn_output/$name

mkdir -p $run_dir 2>/dev/null
mkdir threaded_designs 2>/dev/null


/net/software/containers/mlfold.sif /net/databases/lab/mpnn/github_repo/protein_mpnn_run.py --out_folder $run_dir --num_seq_per_target $n_outputs --pdb_path $pdb --omit_AAs C --pack_side_chains 1 --num_packs 1 --sampling_temp "0.1"


for j in $run_dir/packed/*.pdb; do
    new_name=$(basename $j .pdb | sed -E 's/_seq_([0-9]+)_packed.*/_mpnn\1/g')
    cp $j threaded_designs/$new_name.pdb
done

