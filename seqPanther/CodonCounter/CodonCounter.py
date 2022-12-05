#!/usr/bin/env python
import tempfile
import itertools

from os import path
from glob import glob
from shutil import rmtree
from functools import partial
import click
import numpy as np
import pandas as pd

from Bio import SeqIO
import pyfaidx
import matplotlib.backends.backend_pdf as bpdf
from pylab import *

from . import auto_cpu, bammer, coors_with_changes, gff_reader

__author__ = "Anmol Kiran"
__organisation__ = (
    "Malawi-Liverpool-Wellcome Trust, Malawi; University of Liverpool, UK")
__github__ = "codemeleon"
__email__ = "akiran@mlw.mw"
__version__ = "0.0.2"


def str2coors(coorstr):
    """Converts comma separated values to coordinates and coordinate ranges."""
    coorslist = [x.strip() for x in coorstr.split(',')]
    try:
        coorrange = []
        for coor in coorslist:
            if '-' in coor:
                start, end = coor.split("-")
                coorrange.append([int(start), int(end) + 1])
                pass
            else:
                coorrange.append([int(coor), int(coor) + 1])
        return coorrange
    except:
        exit(
            "Coordinate accept only , and - as alpha numeric values. Please check your coordinate input"
        )


@click.command()
@click.option(
    "-bam",
    help="Bam files",
    # default="/home/devil/Documents/Tools/BitterBits/src/test_data/"
    # "K032623-rep-consensus_alignment_sorted.REF_NC_045512.2.bam",
    # default="./test_data/NC_045512.2.sorted.bam",
    # default="./test_data/InDel/K011018-NC_045512.2_1-consensus_alignment_sorted.bam",  # Deletion
    default="test_data/InDel/Insert/SRR17051909.sorted.bam",  # Inserttion
    type=click.Path(exists=True),
    required=True,
    show_default=True,
)
@click.option(
    "-rid",
    help="Reference ID",
    type=str,
    default="NC_045512.2",
    required=True,
    show_default=True,
)
@click.option(
    "-ref",
    help="Reference fasta files",
    type=str,  # click.File("r"),
    default="./test_data/NC_045512.2.fasta",
    required=True,
    # default="./test_data/NC_045512.2_rev_comp.fasta",
    show_default=True,
)
@click.option(
    "-coor_range",
    help="Coordinates in the reference, zero index based, end exclusive",
    type=str,
    # default="21000-25000", #  Forward sub
    # default="4900-9000", # Reverse sub
    # default="22279-22300",  # For Deletion position
    default="22190-22206",  # Forward insert
    show_default=True,
)
@click.option(
    "--output_type",
    help="Output type",
    type=click.Choice(["nuc", "codon", "both"]),
    default="codon",
    show_default=True,
)
@click.option(
    "-gff",
    help="Gff Annotation File",
    type=click.File("r"),
    default="/home/devil/Documents/Tools/BitterBits/src/test_data/genemap.gff",
    required=True,
    # default="./test_data/genemap_rev_complement.gff",
    show_default=True,
)
@click.option(
    "--ignore_orphans",
    help="Ignore orphaned (Unpaired) reads",
    type=bool,
    default=False,
    show_default=True,
)
@click.option(
    "--min_mapping_quality",
    help="Mapping quality of reads",
    type=int,
    default=0,
    show_default=True,
)
@click.option(
    "--min_base_quality",
    help="Minimum base quality for correct base call",
    type=int,
    default=0,
    show_default=True,
)
@click.option(
    "--ignore_overlaps",
    help="Ignore paired overlapping reads",
    type=bool,
    default=False,
    show_default=True,
)
@click.option(
    "--sort_index",
    help="Sort and index bam file",
    type=bool,
    default=False,
    show_default=True,
)
# TODO: Add samfiles relates conditions
@click.option(
    "--min_seq_depth",
    help="Minimum sequencing depth at position to be considred",
    type=int,
    default=20,
    show_default=True,
)
@click.option(
    "--alt_nuc_count",
    help="Minimum alternate nucleotide count fraction",
    type=click.FloatRange(0.003, 0.5),
    default=0.03,
    show_default=True,
)
@click.option(
    "-n",
    "--cpu",
    "cpu",
    help="Number of CPUs to use",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "-c",
    "--codoncountfile",
    "codoncountfile",
    help="Ouput codon counting CSV File",
    type=click.File("w"),
    default="codon_output.csv",
    show_default=True,
)
@click.option("-e",
              "--endlen",
              "endlen",
              help="Ingnore mismached around the end of reads",
              type=int,
              default=5,
              show_default=True)
@click.option(
    "-s",
    "--subcountfile",
    "subcountfile",
    help="Ouput  subsubstitution counting CSV File",
    type=click.File("w"),
    default="sub_output.csv",
    show_default=True,
)
@click.option(
    "-i",
    "--indelcountfile",
    "indelcountfile",
    help="Ouput  subsubstitution counting CSV File",
    type=click.File("w"),
    default="indel_output.csv",
    show_default=True,
)
def run(
        bam,
        rid,
        coor_range,
        ref,
        output_type,  # TODO:Integrate in main code
        gff,
        ignore_orphans,
        min_mapping_quality,
        min_base_quality,
        ignore_overlaps,
        sort_index,
        min_seq_depth,
        alt_nuc_count,
        cpu,
        endlen,
        codoncountfile,
        subcountfile,
        indelcountfile):
    """Expected to that bam file is sorted based on coordinate and indexed."""

    gff_data = gff_reader.gff2tab(gff)  # gff to pandas dataframe
    if rid not in gff_data["seq_id"].unique():  # Checking presence of given id
        exit("Reference sequence is not in gff file.\n"
             f"References in the gff file {gff_data['seq_id'].unique()}\n"
             "Exiting")
    else:
        gff_data = gff_data[gff_data["seq_id"] ==
                            rid]  # Filtering gff dataframe

    # reference sequence
    try:
        ref_seq = pyfaidx.Fasta(ref)
    except:
        exit(f"{ref} is not in fasta format. Exiting. . . .")
    try:
        ref_seq = ref_seq[rid]
    except:
        exit(f"Reference ID {rid} is not in fasta file {ref}")

    # Listing bam files
    bam_files = None

    if path.isdir(bam):
        bam_files = glob(f"{bam}/*.bam")
        if not bam_files:
            exit("No bam files found in the given directory.\n"
                 f"Directory: {bam}\n"
                 "Exiting")
    elif path.isfile(bam) and bam.endswith(".bam"):
        bam_files = [bam]
    else:
        exit("Bam file is not in the correct format.\n"
             "Exiting")

    # Sorting and indexing bam files
    tmp_dir = tempfile.mkdtemp()
    for i, bam in enumerate(bam_files):
        bam_files[i] = bammer.check_sort_and_index_bam(bam, tmp_dir=tmp_dir)

    # NOTE: genomic range
    coor_range = str2coors(coor_range)

    pool = auto_cpu.cpus(cpu)  # CPU Selection

    codon_related = []
    nuc_sub_related = []
    nuc_indel_related = []
    # Parameter to select reads
    for start, end in coor_range:
        # changes = []
        # TODO: Shift the bottom part and merge in single table

        params = {
            "rid": rid,
            "start": start,
            "end": end,
            "gff_data": gff_data,
            "output_type": output_type,
            "ref": ref,
            "endlen": endlen,
            "ignore_orphans": ignore_orphans,
            "min_mapping_quality": min_mapping_quality,
            "min_seq_depth": min_seq_depth,
            "min_base_quality": min_base_quality,
            "ignore_overlaps": ignore_overlaps,
            "alt_nuc_count": alt_nuc_count,
        }

        changes = partial(coors_with_changes.coor_with_changes_run, params)
        changes = pool.map(changes, bam_files)

        pdf = bpdf.PdfPages("output.pdf")

        for cng in changes:
            if output_type in ["codon", "both"]:
                codon_related.append(cng[0])
            if output_type in ["nuc", "both"]:
                nuc_sub_related.append(cng[1][0])
                nuc_indel_related.append(cng[1][1])
            indel = cng[1][1]
            ins = indel[indel["indel"] > 1]
            delt = indel[indel["indel"] < 1]
            for key, value in cng[-1].items():
                fig = figure(figsize=(8, 6))
                value.index = value.pos
                value = value.reindex(
                    np.arange(value.pos.min(),
                              value.pos.max() + 1)).fillna(0)
                fill_between(value.index,
                             y1=value.depth,
                             y2=0,
                             alpha=0.5,
                             color='gray',
                             linewidth=0)
                value.to_csv("testxxx.csv")
                sub = value[value.pos.isin(cng[1][0].pos)]
                scatter(sub["pos"],
                        sub["depth"],
                        color="green",
                        label="Substitutions",
                        alpha=0.4,
                        s=10)

                inst = value[value.pos.isin(ins.coor)]
                scatter(inst["pos"],
                        inst["depth"],
                        color="red",
                        label="Insertions",
                        alpha=0.4,
                        s=10)
                deltt = value[value.pos.isin(delt.coor)]
                scatter(deltt["pos"],
                        deltt["depth"],
                        color="blue",
                        label="Deletions",
                        alpha=0.4,
                        s=10)
                title(key)
                legend()

                yscale('log')
                pdf.savefig(fig)

        pdf.close()

    if output_type in ["codon", "both"]:

        codon_related = pd.concat(codon_related)
        if len(codon_related):

            codon_related.insert(0, "Reference ID", rid)
            columns = list(codon_related.columns)
            columns.remove("Sample")
            columns = ["Sample"] + columns

            codon_related = codon_related[columns]
            del codon_related["total_codon_count"]
            codon_related.to_csv(
                codoncountfile,
                index=False,
                sep="\t" if codoncountfile.name.endswith(".tsv") else ",")

    if output_type in ["nuc", "both"]:
        nuc_sub_related = pd.concat(nuc_sub_related)
        if len(nuc_sub_related):
            nuc_sub_related = nuc_sub_related.rename(
                columns={
                    'base_count': 'Nucleotide Frequency',
                    'base_pt': 'Nucleotide Percent',
                    'ref_base': 'Reference Nucleotide',
                    'sample': 'Sample'
                })
            nuc_sub_related.insert(0, "Reference ID", rid)

            nuc_sub_related[[
                "Sample", "Reference ID", "pos", "Reference Nucleotide",
                "read_count", "Nucleotide Frequency", "Nucleotide Percent"
            ]].to_csv(subcountfile,
                      index=False,
                      sep="\t" if subcountfile.name.endswith(".tsv") else ",")
        if len(nuc_indel_related):
            nuc_indel_related = pd.concat(nuc_indel_related)
            nuc_indel_related["tp"] = "ins"
            nuc_indel_related.loc[nuc_indel_related["indel"] < 0, "tp"] = "del"
            nuc_indel_related["indelx"] = nuc_indel_related.apply(
                lambda x:
                f"{x['tp']}{x['seq']}:{x['indel_read_count']},read_count:{x['depth']}",
                axis=1)
            nuc_indel_related["indely"] = nuc_indel_related.apply(
                lambda x: f"{'%0.2f' % x['indel_read_pt']}", axis=1)
            nuc_indel_related = nuc_indel_related.drop(
                [
                    "indel", "seq", "indel_read_count", "depth",
                    "indel_read_pt", "tp"
                ],
                axis=1).rename(
                    columns={
                        "indelx": "Nucleotide Frequency",
                        "indely": "Nucleotide Percent",
                        "sample": "Sample"
                    })
            nuc_indel_related.insert(0, "Reference ID", rid)

            nuc_indel_related[[
                "Sample", "Reference ID", "coor", "Nucleotide Frequency",
                "Nucleotide Percent"
            ]].to_csv(
                indelcountfile,
                index=False,
                sep="\t" if indelcountfile.name.endswith(".tsv") else ",")


if __name__ == "__main__":
    run()