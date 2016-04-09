# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""AST Helpers to transform nodes and explore transformations"""

import ast

from .ast_elements import L

class ReplaceContextWithLoad(ast.NodeTransformer):
    """Replace expr_context from any node to Load context"""

    def visit_Attribute(self, node):                                             # pylint: disable=invalid-name
        """Visit Attribute"""
        return ast.copy_location(ast.Attribute(
            self.visit(node.value), node.attr, L()
        ), node)

    def visit_Subscript(self, node):                                             # pylint: disable=invalid-name
        """Visit Subscript"""
        return ast.copy_location(ast.Subscript(
            self.visit(node.value), self.visit(node.slice), L()
        ), node)

    def visit_Name(self, node):                                                  # pylint: disable=invalid-name, no-self-use
        """Visit Name"""
        return ast.copy_location(ast.Name(
            node.id, L()
        ), node)

    def visit_List(self, node):                                                  # pylint: disable=invalid-name
        """Visit List"""
        return ast.copy_location(ast.List(
            [self.visit(elt) for elt in node.elts], L()
        ), node)

    def visit_Tuple(self, node):                                                 # pylint: disable=invalid-name
        """Visit Tuple"""
        return ast.copy_location(ast.Tuple(
            [self.visit(elt) for elt in node.elts], L()
        ), node)

    def visit_Starred(self, node):                                               # pylint: disable=invalid-name
        """Visit Starred"""
        return ast.copy_location(ast.Starred(
            self.visit(node.value), L()
        ), node)


class DebugVisitor(ast.NodeVisitor):
    """Debug ast tree"""

    def visit_expr(self, node):
        """Just visit expr"""
        return self.generic_visit(node)

    def _visit_expr(self, node):
        """Just visit expr"""
        return self.visit_expr(node)

    visit_BoolOp = _visit_expr
    visit_BinOp = _visit_expr
    visit_UnaryOp = _visit_expr
    visit_Lambda = _visit_expr
    visit_IfExp = _visit_expr
    visit_Dict = _visit_expr
    visit_Set = _visit_expr
    visit_ListComp = _visit_expr
    visit_SetComp = _visit_expr
    visit_DictComp = _visit_expr
    visit_GeneratorExp = _visit_expr
    visit_Await = _visit_expr
    visit_Yield = _visit_expr
    visit_YieldFrom = _visit_expr
    visit_Compare = _visit_expr
    visit_Call = _visit_expr
    visit_Num = _visit_expr
    visit_Str = _visit_expr
    visit_Bytes = _visit_expr
    visit_Ellipsis = _visit_expr
    visit_Attribute = _visit_expr
    visit_Subscript = _visit_expr
    visit_Starred = _visit_expr
    visit_Name = _visit_expr
    visit_List = _visit_expr
    visit_Tuple = _visit_expr


def debug_tree(tree, just_print=None, show_code=None, methods=None):
    """Debug ast tree

    Arguments:
    just_print: list of ast node types that should be printed
    show_code: list of ast node types that should be printed and unparsed
    methods: dict of custom functions
    """
    just_print = just_print or []
    show_code = show_code or []
    methods = methods or {}

    def visit_print(self, node):
        """visit node"""
        print(node)
        return self.generic_visit(node)

    def visit_code(self, node):
        """visit node"""
        print(node)
        import astunparse
        print(astunparse.unparse(node))
        return self.generic_visit(node)

    for node_type in just_print:
        methods["visit_" + node_type] = visit_print

    for node_type in show_code:
        methods["visit_" + node_type] = visit_code

    visitor = type('Debugger', (DebugVisitor,), methods)()
    visitor.visit(tree)