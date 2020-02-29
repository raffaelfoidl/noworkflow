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

from .command import ProvOCommand


class ProvO(ProvOCommand):
    """Show the collected provenance of a trial"""

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
        self.add_provo_export_args()
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

        if args.file is None:
            args.file = "trial{}".format(trial.id)

        args.recursion_depth = max(args.recursion_depth, 0)
        self.validate_export_params(args.format, args.graph_dir)

        io.verbose = args.verbose
        export_writer.export_provo(trial, args, self.get_extension(args.format))
