# SeqPanther

SeqPanther tool consists set of commands as follows:

*   **seqpatcher** : integrates sanger sequencing of missing regions of an incomplete assembly to the assembly. This command is modification of [SeqPatcher tool](https://github.com/krisp-kwazulu-natal/seqPatcher)

*   **codoncounter** : performs variant calling, generates nucleotide stats at variant sites and reports impacts of nucleotide changes on amino acids in the translated proteins.

*   **transform** : performs transformation of codoncounter output in a format where user can select variant to integrate in the reference or assemblies using **nucsub** command.

*   **nucsub** : integrates the alteration list generated by codoncounter in a given reference or assembled genome based on the user recommendations. <!--Providing options to users to select changes of their interests-->

## Operating system compatibility

Unix platforms.

## Dependencies

The tool relies on multiple external programs and python modules as listed below:

### External Tools

1.  Muscle

*   To perform multiple sequence alignment
*   Can be downloaded and install from
*   `conda install muscle` to install

2.  BLAT

*   To query sequence location in the genome.
*   `conda install blat` to install

## Python modules

<!-- TODO: Versions need to be included -->

All the python module used for this program is listed in `requirements.txt`.

# Installation

## Manual installation

1.  `pip install -r requirements.txt`
2.  `python setup.py install`

## Directly from the repo

`pip install git+https://github.com/codemeleon/seqPanther.git`

# Usages

The commands are selft explanatory.

seqPanther contains three commands, which can be accessed using `seqPanther --help`

## CodonCounter

This command can be used as `seqPanther CodonCounter`. The help accessible at `seqPanther CodonCounter --help` or [CodonCounter GitHub page](https://github.com/codemeleon/CodonCounter)

## SeqIn

This command can be used as `seqPanther SeqIn`. The help accessible at `seqPanther SeqIn --help` or [SeqIn GitHub page](https://github.com/codemeleon/SeqIn)

## SeqPatcher

This command can be used as `seqPanther SeqPatcher`. The help accessible at `seqPanther SeqPatcher --help` or [SeqPatcher GitHub page](https://github.com/CERI-KRISP/SeqPatcher)

# Features

Codon Counter and SeqIn commands were specifically defined for this program. However, each sub-command can be installed and used independently of this program.

# Bug reporting

Please report bugs on this portal or associated GitHub repos of the command

# Cite

If you use this tool, please cite it as

    Bib for the opensource software journal (JOSS)