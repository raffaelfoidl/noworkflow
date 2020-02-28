# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""'now dataflow'command"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import os

from ..persistence.models.graphs.dependency_graph import DependencyConfig
from ..persistence.models.graphs.dependency_graph import variable_id
from ..persistence.models import Trial
from ..persistence import persistence_config

from .command import Command


class Dataflow(Command):
    """Export dataflow of a trial to dot file"""

    def add_arguments(self):
        add_arg = self.add_argument

        DependencyConfig.create_arguments(add_arg)
        add_arg("-v", "--value-length", type=int, default=0,
                help="R|maximum length of values (default: 0)\n"
                     "0 indicates that values should be hidden.\n"
                     "The values appear on the second line of node lables.\n"
                     "E.g. if it is set to '10', it will show 'data.dat',\n"
                     "but it will transform 'data2.dat' in to 'da...dat'\n"
                     "to respect the length restriction (note that '' is\n"
                     "part of the value).\n"
                     "Minimum displayable value: 5. Suggested: 55.")
        add_arg("-n", "--name-length", type=int, default=55,
                help="R|maximum length of names (default: 55)\n"
                     "0 indicates that values should be hidden.\n"
                     "Minimum displayable value: 5. Suggested: 55.")
        add_arg("-f", "--filter", type=str,
                help="R|filter dataflow by a variable/file name.\n"
                     "It requires pyswip.")
        add_arg("trial", type=str, nargs="?",
                help="trial id or none for last trial")
        add_arg("--dir", type=str,
                help="set project path where is the database. Default to "
                     "current directory")
        add_arg("--content-engine", type=str,
                help="set the content database engine")

    def execute(self, args):
        persistence_config.content_engine = args.content_engine
        persistence_config.connect_existing(args.dir or os.getcwd())
        trial = Trial(trial_ref=args.trial)
        trial.dependency_config.read_args(args)
        trial.dot.value_length = args.value_length
        trial.dot.name_length = args.name_length
        if args.filter:
            query = (
                "var_name({trial}, X, '{filter}'), slice({trial}, X, Y)"
                .format(trial=args.trial, filter=args.filter)
            )
            trial.prolog.use_cache = True
            result = trial.prolog.query(query)

            trial.dependency_filter.run()
            dfilter = trial.dependency_filter
            filtered_variables = []
            for values in result:
                for dependency in values["Y"]:
                    if isinstance(dependency, int):
                        filtered_variables.append(
                            variable_id(dfilter.variables[dependency]))
                    else:
                        filtered_variables.append("a_" + dependency.value[1:])
            dfilter.filtered_variables = filtered_variables
            trial.dot.run = False

        print(trial.dot.export_text())
