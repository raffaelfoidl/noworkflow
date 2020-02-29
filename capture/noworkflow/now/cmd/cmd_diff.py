# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""'now diff' module"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import os

from future.utils import viewitems, viewkeys

from ..ipython.converter import create_ipynb
from ..persistence.models.diff import Diff as DiffModel
from ..persistence import persistence_config
from ..utils.io import print_msg
from ..utils.cross_version import zip_longest

from .cmd_show import print_trial_relationship
from .command import NotebookCommand

import noworkflow.now.persistence.provo.diff.diff_writer as diff_writer


def print_diff_trials(diff, skip=None):
    """Print diff of basic trial information"""
    skip = skip or set()
    for key, values in viewitems(diff.trial):
        if key not in skip:
            print("  {} changed from {} to {}".format(
                key.capitalize().replace("_", " "),
                values[0] or "<None>", values[1] or "<None>"))
    print()


def print_replaced_attributes(replaced, ignore=("id",), extra=tuple(),
                              names=None):
    """Print attributes diff"""
    names = names or {}
    for (removed, added) in replaced:
        print("  Name: {}".format(removed.name))
        output = []
        for key in viewkeys(removed.to_dict(ignore=ignore, extra=extra)):
            removed_attr = getattr(removed, key)
            added_attr = getattr(added, key)
            if removed_attr != added_attr:
                output.append("    {} changed from {} to {}".format(
                    names.get(key, key.capitalize().replace("_", " ")),
                    removed_attr or "<None>", added_attr or "<None>"))
        print("\n".join(output))
        print()


def print_replaced_environment(replaced):
    """Print environment diff"""
    for (attr_removed, attr_added) in replaced:
        print("  Environment attribute {} changed from {} to {}".format(
            attr_removed.name,
            attr_removed.value or "<None>",
            attr_added.value or "<None>"))


def print_brief(added, removed, replaced):
    """Print brief diff"""
    added_names = [access.brief for access in added]
    removed_names = [access.brief for access in removed]
    replaced_names = [rem.brief for rem, add in replaced]
    order = added_names, removed_names, replaced_names
    for column in order:
        column.sort()
    added_names.insert(0, "[Additions]")
    removed_names.insert(0, "[Removals]")
    replaced_names.insert(0, "[Changes]")
    max_column_len = [max(len(text) for text in column)
                      for column in order]

    # max_len = max(len(column) for column in order)
    for add, rem, cha in zip_longest(*order):
        add = add or ""
        rem = rem or ""
        cha = cha or ""
        print('{0: <{3}} | {1: <{4}} | {2: <{5}}'.format(
            add, rem, cha, *max_column_len))


def hide_timestamp(elements):
    """Set hide_timestamp of elements"""
    for element in elements:
        element.hide_timestamp = True


def print_diff(access_extra, args, diff, skip_in_trial):
    print_msg("trial diff:", True)
    print_diff_trials(diff, skip=skip_in_trial)
    if args.modules:
        (added, removed, replaced) = diff.modules
        if args.brief:
            print_msg("Brief modules diff", True)
            print_brief(added, removed, replaced)
        else:
            print_msg("{} modules added:".format(len(added)), True)
            print_trial_relationship(added)
            print()

            print_msg("{} modules removed:".format(len(removed)), True)
            print_trial_relationship(removed)
            print()

            print_msg("{} modules replaced:".format(len(replaced)), True)
            print_replaced_attributes(replaced)
        print()
    if args.environment:
        (added, removed, replaced) = diff.environment
        if args.brief:
            print_msg("Brief environment attributes diff", True)
            print_brief(added, removed, replaced)
        else:
            print_msg("{} environment attributes added:".format(
                len(added)), True)
            print_trial_relationship(added, breakline="\n", other="\n  ")
            print()

            print_msg("{} environment attributes removed:".format(
                len(removed)), True)
            print_trial_relationship(removed, breakline="\n", other="\n  ")
            print()

            print_msg("{} environment attributes replaced:".format(
                len(replaced)), True)
            print_replaced_environment(replaced)
        print()
    if args.file_accesses:
        (added, removed, replaced) = diff.file_accesses
        if args.brief:
            print_msg("Brief file access diff", True)
            print_brief(added, removed, replaced)
        else:
            if args.hide_timestamps:
                hide_timestamp(added)
                hide_timestamp(removed)
            print_msg("{} file accesses added:".format(
                len(added)), True)
            print_trial_relationship(added)
            print()

            print_msg("{} file accesses removed:".format(
                len(removed)), True)
            print_trial_relationship(removed)
            print()

            print_msg("{} file accesses replaced:".format(
                len(replaced)), True)
            print_replaced_attributes(
                replaced,
                extra=access_extra,
                ignore=("id", "trial_id", "function_activation_id"),
                names={"stack": "Function"})


class Diff(NotebookCommand):
    """Compare the collected provenance of two trials"""

    def add_arguments(self):
        add_arg = self.add_argument
        add_arg("trial1", type=str,
                help="first trial id to be compared")
        add_arg("trial2", type=str,
                help="second trial id to be compared")
        add_arg("-m", "--modules", action="store_true",
                help="compare module dependencies")
        add_arg("-e", "--environment", action="store_true",
                help="compare environment conditions")
        add_arg("-f", "--file-accesses", action="store_true",
                help="compare read/write access to files")
        add_arg("-t", "--hide-timestamps", action="store_true",
                help="hide timestamps (does not apply to -p option)")
        add_arg("--brief", action="store_true",
                help="display a concise version of diff (does not apply to -p option)")
        add_arg("-p", "--provo", action="store_true",
                help="export comparison as prov-o document; suppresses console output")
        add_arg("-n", "--defaultns", type=str, default="https://github.com/gems-uff/noworkflow",
                help="set the default namespace for the exported prov-o file. "
                     "Default: https://github.com/gems-uff/noworkflow")
        add_arg("--dir", type=str,
                help="set project path where is the database. Default to "
                     "current directory")
        add_arg("--content-engine", type=str,
                help="set the content database engine")

    def execute(self, args):
        persistence_config.content_engine = args.content_engine
        persistence_config.connect_existing(args.dir or os.getcwd())
        if args.hide_timestamps:
            skip_in_trial = {"start", "finish", "duration_text"}
            access_extra = ("mode", "buffering", "content_hash_before",
                            "content_hash_after", "stack")
        else:
            skip_in_trial = set()
            access_extra = ("mode", "buffering", "content_hash_before",
                            "content_hash_after", "timestamp", "stack")

        diff = DiffModel(args.trial1, args.trial2)

        if not args.provo:
            print_diff(access_extra, args, diff, skip_in_trial)
        else:
            diff_writer.export_diff(diff, args)

    def execute_export(self, args):
        persistence_config.content_engine = args.content_engine
        persistence_config.connect_existing(args.dir or os.getcwd())
        DiffModel(args.trial1, args.trial2)
        name = "Diff-{0}-{1}.ipynb".format(args.trial1, args.trial2)
        code = ("%load_ext noworkflow\n"
                "import noworkflow.now.ipython as nip\n"
                "# <codecell>\n"
                "diff = nip.Diff('{0}', '{1}')\n"
                "# diff.graph.view = 0\n"
                "# diff.graph.mode = 3\n"
                "# diff.graph.width = 500\n"
                "# diff.graph.height = 500\n"
                "# <codecell>\n"
                "diff").format(args.trial1, args.trial2)
        create_ipynb(name, code)
