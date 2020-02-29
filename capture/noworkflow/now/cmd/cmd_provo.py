# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""'now provo' command"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import os
import sys
from collections import OrderedDict

from noworkflow.now.persistence.provo.export import export_writer
from ..persistence.models import Trial
from ..persistence import persistence_config
from ..utils import io

from .command import Command
from ..utils.io import print_msg


class ProvO(Command):
    """Show the collected provenance of a trial"""

    output_formats = OrderedDict(
        [("provn", ".pn"), ("xml", ".xml"), ("rdf", ".rdf"), ("json", ".json"), ("pdf", ".pdf"), ("svg", ".svg"),
         ("dot", ".gv"), ("png", ".png"), ("jpeg", ".jpeg")])

    def add_arguments(self):
        add_arg = self.add_argument
        add_arg("trial", type=str, nargs="?",
                help="trial id or none for last trial")
        add_arg("-m", "--modules", action="store_true",
                help="shows module dependencies")
        add_arg("-d", "--function-defs", action="store_true",
                help="shows the user-defined functions")
        add_arg("-e", "--environment", action="store_true",
                help="shows the environment conditions")
        add_arg("-a", "--function-activations", action="store_true",
                help="shows function activations")
        add_arg("-f", "--file-accesses", action="store_true",
                help="shows read/write access to files")
        add_arg("-r", "--recursion-depth", type=int, default=0,
                help="Sets the maximum recursion depth when analyzing function calls within function calls. Any value"
                     "less than 1 results in no restriction (besides maximum stack size). Default: 0")
        add_arg("--filename", type=str,
                help="Set the name or path of the prov-o file to export (without extension). "
                     "Default: <currDir>/trial<No.>")
        add_arg("--format", type=str, default=list(self.output_formats.items())[0][0],
                help="set the format of the exported prov-o file; allowed values {" + ", ".join(self.output_formats) +
                     "}}. Default: {}".format(list(self.output_formats.items())[0][0]))
        add_arg("-n", "--defaultns", type=str, default="https://github.com/gems-uff/noworkflow",
                help="set the default namespace for the exported prov-o file. "
                     "Default: https://github.com/gems-uff/noworkflow")
        add_arg("--hide-elem-attr", action="store_true",
                help="Hide element attributes in a graph to be rendered. Default: not hidden (= option not specified)")
        add_arg("--hide-rel-attr", action="store_true",
                help="Hide relation attributes in a graph to be rendered. Default: not hidden (= option not specified)")
        add_arg("-g", "--graph-dir", type=str, default="BT",
                help="Specify direction of a graph to be rendered. Allowed values: {BT, TB, LR, RL}. Default: BT")
        add_arg("-v", "--verbose", action="store_true",
                help="increase output verbosity")
        add_arg("--dir", type=str,
                help="set project path where is the database. Default to "
                     "current directory")
        add_arg("--content-engine", type=str,
                help="set the content database engine")

    def execute(self, args):
        persistence_config.content_engine = args.content_engine
        persistence_config.connect_existing(args.dir or os.getcwd())
        trial = Trial(trial_ref=args.trial)

        if args.filename is None:
            args.filename = "trial{}".format(trial.id)

        args.recursion_depth = max(args.recursion_depth, 0)
        self.validate_params(args.format, args.graph_dir)

        io.verbose = args.verbose
        export_writer.export_provo(trial, args, self.output_formats[args.format])

    def validate_params(self, format: str, graph_dir: str):
        if self.output_formats.get(format) is None:
            print_msg("Invalid export format \"{}\". Please consult \"now provo -h\".".format(format), True)
            sys.exit(1)

        if graph_dir.upper() not in ["BT", "TB", "LR", "RL"]:
            print_msg("Invalid graph direction \"{}\". Please consult \"now provo -h\".".format(graph_dir), True)
            sys.exit(1)
