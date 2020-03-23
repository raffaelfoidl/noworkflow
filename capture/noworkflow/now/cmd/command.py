# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Command base"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import argparse
from collections import OrderedDict

from ..utils.functions import abstract


class SmartFormatter(argparse.HelpFormatter):
    """Add option to split lines in help messages"""

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


class Command(object):
    """Command base"""

    def __init__(self, cmd=None):
        self.cmd = cmd or type(self).__name__.lower()
        self.help = self.__doc__.split("\n")[0].strip()
        self.parser = None
        self.add_help = True
        self.is_ipython = False

    def create_parser(self, subparsers):
        """Create parser with arguments"""
        kwargs = {}
        if self.help:
            kwargs["help"] = self.help
        self.parser = subparsers.add_parser(
            self.cmd, add_help=self.add_help, formatter_class=SmartFormatter,
            **kwargs
        )

        self.add_arguments()
        self.parser.set_defaults(func=self.execute)

    def add_arguments(self):
        """Add arguments to command. Override on subclass"""
        pass

    def add_argument(self, *args, **kwargs):
        """Add argument to parser available for both IPython magic and cmd"""
        return self.parser.add_argument(*args, **kwargs)

    def add_argument_cmd(self, *args, **kwargs):
        """Add argument to parser available only for cmd"""
        return self.parser.add_argument(*args, **kwargs)

    def execute(self, args):
        """Execute the command. Override on subclass"""
        abstract()
        print(self, args)


class ProvOCommand(Command):
    output_formats = OrderedDict(
        [("provn", ".pn"), ("turtle", ".ttl"), ("xml", ".xml"), ("rdfxml", ".xml"), ("trig", ".trig"),
         ("json", ".json"), ("pdf", ".pdf"), ("svg", ".svg"), ("dot", ".gv"), ("png", ".png"), ("jpeg", ".jpeg")])

    def add_provo_export_args(self):
        self.add_argument("--file", type=str,
                          help="Set the name or path of the prov-o file to export (without extension). "
                               "Default: <currDir>/trial<No.>")
        self.add_argument("--format", type=str, default=list(self.output_formats.items())[0][0],
                          help="set the format of the exported prov-o file; allowed values {" + ", ".join(
                              self.output_formats) +
                               "}}. Default: {}".format(list(self.output_formats.items())[0][0]))
        self.add_argument("-n", "--defaultns", type=str, default="https://github.com/gems-uff/noworkflow#",
                          help="set the default namespace for the exported prov-o file. "
                               "Default: https://github.com/gems-uff/noworkflow#")
        self.add_argument("--hide-elem-attr", action="store_true",
                          help="Hide element attributes in a graph to be rendered. Default: not hidden (= option not specified)")
        self.add_argument("--hide-rel-attr", action="store_true",
                          help="Hide relation attributes in a graph to be rendered. Default: not hidden (= option not specified)")
        self.add_argument("-g", "--graph-dir", type=str, default="BT",
                          help="Specify direction of a graph to be rendered. Allowed values: {BT, TB, LR, RL}. Default: BT")

    def validate_export_params(self, format: str, graph_dir: str):
        from noworkflow.now.utils.io import print_msg
        import sys

        if self.output_formats.get(format) is None:
            print_msg("Invalid export format \"{}\". Please consult \"now {} -h\"."
                      .format(format, self.__class__.__name__.lower()), True)
            sys.exit(1)

        if graph_dir.upper() not in ["BT", "TB", "LR", "RL"]:
            print_msg("Invalid graph direction \"{}\". Please consult \"now {} -h\"."
                      .format(graph_dir, self.__class__.__name__.lower()), True)
            sys.exit(1)

    def get_extension(self, format: str):
        return self.output_formats.get(format)


class NotebookCommand(Command):
    """NotebookCommand base. Default option -i to export notebook files"""

    def create_parser(self, subparsers):
        """Create parser with arguments"""
        super(NotebookCommand, self).create_parser(subparsers)
        self.add_argument("-i", "--ipynb", action="store_true",
                          help="export jupyter notebook file")
        self.parser.set_defaults(func=self._execute)

    def _execute(self, args):
        """Select between export or execute"""
        if args.ipynb:
            self.execute_export(args)
        else:
            self.execute(args)

    def execute_export(self, args):
        """Export notebook file. Override on subclass"""
        abstract()
        print(self, args)
