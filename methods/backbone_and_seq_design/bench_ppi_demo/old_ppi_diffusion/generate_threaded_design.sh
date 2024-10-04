#!/bin/bash

pdb=$1
hotspots=$2
contig=$3
n_backbones=$4
n_mpnn=$5

mkdir backbones 2>/dev/null


# Contigs come with underscores but diffusion wants spaces
contig=$(echo $contig | tr '_' ' ')

# Make the temporary diffusio noutput directory
name=$(basename $pdb .pdb)
out_dir=diffusion_out/$name
mkdir -p $out_dir 2>/dev/null


diffusion_script=/software/lab/diffusion/rf_diffusion/run_inference.py
checkpoint=/databases/diffusion/models/hotspot_models/base_complex_finetuned_BFF_9.pt

# Pretty standard PPI diffusion command
apptainer exec --nv /software/containers/SE3nv.sif python $diffusion_script --config-name=base \
    inference.output_prefix=$out_dir/${name}_bb \
    inference.input_pdb=$pdb \
    ppi.hotspot_res=[$hotspots] \
    contigmap.contigs=["'""$contig""'"] \
    inference.final_step=5 \
    inference.ckpt_override_path=$checkpoint \
    inference.num_designs=$n_backbones \
    denoiser.noise_scale_ca=0 \
    denoiser.noise_scale_frame=0 \
    potentials.guide_scale=0 \
    diffuser.T=50


# move pdbs to backbones/ and generate mpnn sequences
for j in $out_dir/*.pdb; do
    new_name=$(basename $j .pdb | sed 's/bb_/bb/g')
    new_path=backbones/$new_name.pdb
    cp $j $new_path
    ./scripts/generate_threaded_design_from_backbone.sh $new_path $n_mpnn
done



