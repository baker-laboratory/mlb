#!/usr/bin/env python

import os
import sys
import argparse
import pandas as pd
import numpy as np
import re
from collections import defaultdict
import itertools

from pyrosetta import *
from pyrosetta.rosetta import *

init('-mute all -beta_nov16')

sys.path.append('/software/lab/npose')
import npose_util as nu
import npose_util_pyrosetta as nup

sys.path.append("/databases/lab/motif_hash/getpy_motif/")
import motif_stuff2


parser = argparse.ArgumentParser()
parser.add_argument("--inputs_txt", type=str, default="inputs.txt")
parser.add_argument("--af2_outputs", type=str, nargs="+")
parser.add_argument("--af2_scores", type=str, default='oracle_outputs/af2_scores.sc')

args = parser.parse_args(sys.argv[1:])


# Parse inputs.txt into the format we need it
target_to_info = {}
all_hotspot_sets = set()
with open(args.inputs_txt) as f:
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        sp = line.split()
        assert len(sp) == 5, sp

        pdb, hotspots_diffusion, contig, _, _ = sp

        d = dict(pdb=pdb, hotspots_diffusion=hotspots_diffusion)
        target = os.path.basename(pdb).replace('.pdb', '')

        hotspots_ros = []
        pose = pose_from_file(pdb)
        for dif_hot in hotspots_diffusion.split(','):
            chain = dif_hot[0]
            number = int(dif_hot[1:])

            for seqpos in range(1, pose.size()+1):
                if pose.pdb_info().chain(seqpos) == chain and pose.pdb_info().number(seqpos) == number:
                    hotspots_ros.append(seqpos)

        d['hotspots_ros'] = ','.join(str(x) for x in hotspots_ros)
        target_to_info[target] = d

        all_hotspot_sets.add(d['hotspots_ros'])



selectors = []
filters = []
names = []

all_hotspot_sets = list(all_hotspot_sets)

selectors.append('<Chain name="chainA" chains="A"/>')
selectors.append('<Chain name="chainB" chains="B"/>')

for i, res_string in enumerate(all_hotspot_sets):

    name = "contact_patch%i"%i
    

    selectors.append(f'<Slice name="{name}" indices="{res_string}" selector="chainB" />')
    filters.append(f'<ContactMolecularSurface name="{name}" distance_weight="0.5" target_selector="{name}"'
                                                                    +' binder_selector="chainA" confidence="0" />')
    names.append(name)


selectors_string = "\n".join(selectors)
filters_string = "\n".join(filters)
xml = f'''
<RESIDUE_SELECTORS>
{selectors_string}
</RESIDUE_SELECTORS>
<FILTERS>
<Sasa name="interface_buried_sasa" confidence="0" />
<ContactMolecularSurface name="contact_molecular_surface" distance_weight="0.5" target_selector="chainA" binder_selector="chainB" confidence="0" />
{filters_string}
</FILTERS>
'''

objs = protocols.rosetta_scripts.XmlObjects.create_from_string(xml)

cp_filters = {}
for name, hotspots in zip(names, all_hotspot_sets):
    cp_filters[hotspots] = objs.get_filter(name)


sasa_filter = objs.get_filter('interface_buried_sasa')
cms_filter = objs.get_filter('contact_molecular_surface')







abego_man = core.sequence.ABEGOManager()
def get_abego(pose, seqpos):
    return abego_man.index2symbol(abego_man.torsion2index_level1( pose.phi(seqpos), pose.psi(seqpos), pose.omega(seqpos)))


def get_consensus(letters):
    counts = defaultdict(lambda : 0, {})
    for letter in letters:
        counts[letter] += 1

    maxx_letter = 0
    maxx = 0
    for key in counts:
        if ( counts[key] > maxx ):
            maxx = counts[key]
            maxx_letter = key
    return maxx_letter



# this is 1 indexed with the start and end with loops converted to nearby dssp
# and HHHHHH turns identified
def better_dssp3(pose, length=-1, force_consensus=None, consensus_size=6):
    if ( length < 0 ):
        length = pose.size()

    dssp = core.scoring.dssp.Dssp(pose)
    dssp.dssp_reduced()
    the_dssp = "x" + dssp.get_dssp_secstruct()[:length]
    the_dssp = list(the_dssp)

    n_consensus = get_consensus(the_dssp[3:consensus_size+1])
    if ( not force_consensus is None ):
        n_consensus = force_consensus

    for i in range(1, consensus_size+1):
        the_dssp[i] = n_consensus

    c_consensus = get_consensus(the_dssp[-(consensus_size):-2])
    if ( not force_consensus is None ):
        c_consensus = force_consensus

    for i in range(1, consensus_size+1):
        the_dssp[-i] = c_consensus

    the_dssp = "".join(the_dssp)

    # print(the_dssp)

    my_dssp = "x"

    for seqpos in range(1, length+1):
        abego = get_abego(pose, seqpos)
        this_dssp = the_dssp[seqpos]
        if ( the_dssp[seqpos] == "H" and abego != "A" ):
            # print("!!!!!!!!!! Dssp - abego mismatch: %i %s %s !!!!!!!!!!!!!!!"%(seqpos, the_dssp[seqpos], abego))

            # This is the Helix-turn-helix HHHH case. See the test_scaffs folder
            if ( (abego == "B" or abego == "E") and seqpos > consensus_size and seqpos < len(the_dssp)-consensus_size ):
                this_dssp = "L"

        my_dssp += this_dssp

    # print(my_dssp)

    return my_dssp



# assumes dssp starts with X and removes it
def get_ss_elements2(dssp):
    assert(dssp[0] == "x")
    ss_elements = []

    offset = 0
    ilabel = -1
    for label, group in itertools.groupby(dssp):
        ilabel += 1
        this_len = sum(1 for _ in group)
        next_offset = offset + this_len

        ss_elements.append( (label, offset, next_offset-1))

        offset = next_offset
    return ss_elements[1:]






# rosetta/main/source/src/core/select/util/SelectResiduesByLayer.cc
def sidechain_neighbors(binder_Ca, binder_Cb, else_Ca):

    conevect = binder_Cb - binder_Ca
    conevect /= np.sqrt(np.sum(np.square(conevect), axis=-1))[:,None]

    vect = else_Ca[:,None] - binder_Cb[None,:]
    vect_lengths = np.sqrt(np.sum(np.square(vect), axis=-1))
    vect_normalized = vect / vect_lengths[:,:,None]

    dist_term = 1 / ( 1 + np.exp( vect_lengths - 9  ) )

    angle_term = (((conevect[None,:] * vect_normalized).sum(axis=-1) + 0.5) / 1.5).clip(0, None)

    sc_neigh = (dist_term * np.square( angle_term )).sum(axis=0)

    return sc_neigh


def move_chainA_far_away(pose):
    pose = pose.clone()
    sel = core.select.residue_selector.ChainSelector("A")
    subset = sel.apply(pose)

    x_unit = numeric.xyzVector_double_t(1, 0, 0)
    far_away = numeric.xyzVector_double_t(10000, 0, 0)

    protocols.toolbox.pose_manipulation.rigid_body_move(x_unit, 0, far_away, pose, subset)

    return pose



scorefxn_beta_soft = core.scoring.ScoreFunctionFactory.create_score_function("beta_nov16_soft")
def calc_ddg_norepack(pose, scorefxn):
    pose = pose.clone()
    
    close_score = scorefxn(pose)
    pose = move_chainA_far_away(pose)
    far_score = scorefxn(pose)

    return close_score - far_score



























def score_ppi_example(pose, hotspots_ros):

    out_scores = {}

    pose_in = pose.clone()

    pose = pose.split_by_chain()[1]

    npose = nup.npose_from_pose(pose)

    dssp = better_dssp3(pose)
    ss_elems = get_ss_elements2(dssp)

    longest_loop = 0
    total_loop = 0
    for h, start, end in ss_elems:
        if ( h != "L" ):
            continue
        size = end - start + 1
        longest_loop = max(size, longest_loop)
        total_loop += size

    out_scores['longest_loop'] = longest_loop

    ca = nu.extract_atoms(npose, [nu.CA])[:,:3]
    cb = nu.extract_atoms(npose, [nu.CB])[:,:3]

    sc_neigh = sidechain_neighbors( ca, cb, ca )

    # is_core = sc_neigh > 5.2
    is_core = sc_neigh > 4.9
    is_surface = sc_neigh < 2


    out_scores['mean_scn'] = sc_neigh.mean()
    out_scores['percent_core_scn'] = is_core.mean()



    hits, froms, tos, misses = motif_stuff2.motif_score_npose( npose )

    froms = np.array(froms)+1
    tos = np.array(tos)+1

    mask = ~is_surface[froms-1] & ~is_surface[tos-1]
    froms = froms[mask]
    tos = tos[mask]

    helix_elems = list(x for x in ss_elems if x[0] == "H")

    micro_helices = 0
    for _, start, end in helix_elems:
        size = end - start + 1
        if ( size < 9 ):
            micro_helices += 1
            # print("color red, resi %i-%i"%(start, end))
    out_scores['micro_helices'] = micro_helices


    ss_elems = list(x for x in ss_elems if x[0] != "L")


    im_in_ss = np.zeros(pose.size()+1, int)
    im_in_ss[:] = -1
    for iss, (_, start, end) in enumerate(ss_elems):
        im_in_ss[start:end+1] = iss

    is_ss = im_in_ss > -1

    scores = []
    scores_sandwich = []
    starts = []
    any_core_in_span = []
    window_size = 9
    for start in range(1, pose.size()+1):
        end = start + window_size - 1
        if ( end > pose.size() ):
            continue

        if ( not is_ss[start:end+1].all() ):
            continue

        our_iss = im_in_ss[start]
        if ( not (our_iss == im_in_ss[start:end+1]).all() ):
            continue


        from_us = (froms >= start) & (froms <= end)
        to_us = (tos >= start) & (tos <= end)

        interesting = (from_us ^ to_us)

        who = np.zeros(len(from_us), np.int)
        who[:] = -2
        who[~from_us] = im_in_ss[froms[~from_us]]
        who[~to_us] = im_in_ss[tos[~to_us]]

        who = who[interesting]
        who = who[who != -1]
        who = who[who != our_iss]
        assert( not np.any(who == -2) )

        unique_who, unique_counts = np.unique(who, return_counts=True)
        argsort = np.argsort(unique_counts)[::-1]
        sorted_who = unique_who[argsort]
        sorted_counts = unique_counts[argsort]

        hits_to_others = 0
        if ( len(sorted_counts) >= 2 ):
            hits_to_others = sorted_counts[1:].sum()


        scores.append(hits_to_others)
        starts.append(start)


        if ( is_core[start-1:end].any() ):
            any_core_in_span.append(1)
        else:
            any_core_in_span.append(0)

    scores = np.array(scores)
    starts = np.array(starts)

    out_scores['other_hits_9'] = (scores >= 1).mean()
    out_scores['any_core_9'] = np.mean(any_core_in_span)



    dssp = better_dssp3(pose)
    ss_elems = get_ss_elements2(dssp)

    my_str = "".join([h for h, start, end in ss_elems if h != "L"])

    out_scores['scaff_dssp'] = my_str

    H = dssp.count('H')
    E = dssp.count('E')
    L = dssp.count('L')
    tot = H + E + L

    out_scores['frac_H'] = H / tot
    out_scores['frac_E'] = E / tot
    out_scores['frac_L'] = L / tot



    pose = pose_in.clone()

    out_scores['ddg_norepack_soft'] = calc_ddg_norepack(pose, scorefxn_beta_soft)


    cp_filter = cp_filters[hotspots_ros]

    out_scores['contact_patch'] = cp_filter.report_sm(pose)

    monomer_size = pose.conformation().chain_end(1)
    npose = nup.npose_from_pose(pose)

    Cbs = nu.extract_atoms(npose, [nu.CB])[:,:3]

    hotspots_idx0 = [int(x) + monomer_size - 1 for x in hotspots_ros.split(',')]

    binder_Cbs = Cbs[:monomer_size]
    hotspot_Cbs = Cbs[hotspots_idx0]

    hotspot_dist_binder = np.linalg.norm( hotspot_Cbs[:,None] - binder_Cbs[None,:], axis=-1)

    hotspot_closest_binder = hotspot_dist_binder.min(axis=-1)
    assert len(hotspot_closest_binder) == hotspots_ros.count(',') + 1

    out_scores['hotspot_satisfied7'] = (hotspot_closest_binder < 7).mean()
    out_scores['hotspot_satisfied10'] = (hotspot_closest_binder < 10).mean()


    out_scores['delta_sasa'] = sasa_filter.report_sm(pose)
    out_scores['contact_molecular_surface'] = cms_filter.report_sm(pose)



    return out_scores













####################### main ##############################



af2_df = pd.read_csv(args.af2_scores, sep='\s+')
af2_df = af2_df.drop_duplicates('description')


results = []

for pdb in args.af2_outputs:
    print("Attempting:", pdb)
    tag = os.path.basename(pdb).replace('.pdb', '')

    target = re.sub('_bb.*', '', tag)
    bb = re.sub('_mpnn.*', '', tag)
    mpnn = re.sub('_oracle', '', tag)

    target_info = target_to_info[target]

    pose = pose_from_file(pdb)

    # reset the numbering to make everything easier
    pose.pdb_info(core.pose.PDBInfo(pose))


    af2_rows = af2_df[af2_df['description'] == tag]
    assert len(af2_rows) == 1, tag

    af2_row = af2_rows.iloc[0]


    out_scores = score_ppi_example(pose, target_info['hotspots_ros'])


    copy_from_af2 = ['plddt_binder', 'pae_interaction', 'binder_rmsd', 'interface_rmsd', 'description']
    for key in copy_from_af2:
        out_scores[key] = af2_row[key]


    out_scores['target'] = target
    out_scores['bb'] = bb
    out_scores['mpnn'] = mpnn
    out_scores['description'] = tag

    # print(out_scores)

    results.append(out_scores)


df = pd.DataFrame(results)



# df = pd.read_csv('score_individual.csv')
df['pass_longxing_monomer'] = (df['other_hits_9'] > 0.85) & (df['any_core_9'] > 0.85) & (df['longest_loop'] < 8)
df['pass_plddt85'] = df['plddt_binder'] > 85
df['pass_plddt90'] = df['plddt_binder'] > 90
df['pass_hotspots'] = df['hotspot_satisfied10'] >= 0.75
df['pass_rmsd'] = df['interface_rmsd'] < 4
df['pass_pae15'] = (df['pae_interaction'] < 15) & df['pass_rmsd'] & df['pass_hotspots']
df['pass_pae10'] = (df['pae_interaction'] < 10) & df['pass_rmsd'] & df['pass_hotspots']
df['pass_pae5'] = (df['pae_interaction'] < 5) & df['pass_rmsd'] & df['pass_hotspots']


df['excellent'] = df['pass_pae5'] & df['pass_plddt90']
df['orderable'] = df['pass_pae10'] & df['pass_plddt90']
df['almost_orderable'] = df['pass_pae15'] & df['pass_plddt85']

df['excellent_sane'] = df['excellent'] & df['pass_longxing_monomer']
df['orderable_sane'] = df['orderable'] & df['pass_longxing_monomer']
df['almost_orderable_sane'] = df['almost_orderable'] & df['pass_longxing_monomer']

df.to_csv('score_individual.sc', sep=' ', index=None, na_rep='NaN')
df.to_csv('score_individual.csv', index=None, na_rep='NaN')


mean_scores = ['excellent', 'orderable', 'almost_orderable', 'excellent_sane', 'orderable_sane', 'almost_orderable_sane',
                'hotspot_satisfied7', 'hotspot_satisfied10', 'frac_H', 'frac_E', 'frac_L', ]

mean_only_of_almost_orderable = ['ddg_norepack_soft', 'contact_patch', 'delta_sasa', 'contact_molecular_surface']


summary_results = {}

for term in mean_scores:
    summary_results[term] = df[term].mean()


for term in mean_only_of_almost_orderable:
    each_target = []
    for target, subdf in df.groupby('target'):
        subdf = subdf[subdf['almost_orderable']]
        if len(subdf) == 0:
            each_target.append(np.nan)
        else:
            each_target.append(subdf[term].mean())

    summary_results[term] = np.mean(each_target)


print(summary_results)

summary_df = pd.DataFrame([summary_results])
summary_df.to_csv('final_scores.csv', index=None, na_rep='NaN')
summary_df.to_csv('final_scores.sc', index=None, sep=' ', na_rep='NaN')
























