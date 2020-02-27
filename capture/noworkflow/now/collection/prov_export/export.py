import itertools
from collections import Counter

import prov.model as provo
import datetime

from noworkflow.now.persistence.models import Trial, Module
from noworkflow.now.utils.functions import wrap
from noworkflow.now.utils.io import print_msg

OPERATIONS = ("add", "sub", "mult", "div", "mod", "pow", "floordiv",  # arithmetic operators
              "add_assign", "sub_assign", "mult_assign", "div_assign",  # assignment operators 1
              "mod_assign", "pow_assign", "floordiv_assign",  # assignment operators 2
              "bitand_assign", "bitor_assign", "bitxor_assign",  # assignment operators 3
              "rshift_assign", "lshift_assign",  # assignment operators 4
              "eq", "noteq", "gt", "lt", "gte", "lte",  # comparison operators
              "and", "or", "not",  # logical operators
              "is", "isnot",  # identity operators
              "in", "notin",  # membership operators
              "bitand", "bitor", "bitxor", "invert", "rshift", "lshift"  # bitwise operators
              )


def escape(string):
    forbidden = ["=", "'", "(", ")", ",", "_", ":", ";", "[", "]", "/",
                 "\\", "?", "@", "~", "&", "+", "*", "#", "$", "^", "!", "<", ">", "%"]

    return_value = string
    for char in forbidden:
        return_value = return_value.replace(char, "_")

    return return_value


def entity_name(evaluation):
    component = evaluation.code_component
    ent_name_str = ""

    if component.type in ("name", "literal", "param"):
        ent_name_str = str(component.first_char_line) + "_" + component.name
    elif component.type == "subscript":
        ent_name = component.name.split("[")[0]
        ent_name += "@" + component.name.split("[")[1].split("]")[0]
        ent_name_str = str(component.first_char_line) + "_" + ent_name
    else:
        ent_name_str = component.type + str(component.id)

    return escape(ent_name_str)


def entity_type(evaluation):
    component = evaluation.code_component

    if component.type in OPERATIONS:
        return "eval"
    elif component.type == "call":
        return "eval"
    elif component.type == "subscript":
        return "access"
    else:
        return component.type


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def activity_name_label(evals, evaluation_id):
    for ev in evals:
        if ev.id == evaluation_id:
            return ev.code_component.type, ev.code_component.name.split("(")[0]


def find_collection_name(trial, assignments, evaluation_id):
    for dep in trial.dependencies:
        if dep.dependent_id == evaluation_id and dep.type == "value":
            dependency = entity_name(dep.dependency)
            if dependency in assignments:
                dependency = assignments[dependency]
            return dependency
    return None


def print_trial_relationship(relation, breakline="\n\n", other="\n    "):
    """Print trial relationship"""
    output = []
    for obj in relation:
        obj.show(_print=lambda x: output.append(wrap(x, other=other)))
    print(breakline.join(output))


def export_module_deps(trial, document: provo.ProvDocument):
    print_msg("Exporting module dependencies", True)
    for module in trial.modules:  # type: Module
        document.entity("module{}".format(module.id),
                        [(provo.PROV_LABEL, module.name),
                         ("version", module.version),
                         ("path", module.path),
                         ("codeHash", module.code_hash)])


def print_function_activation(trial, activation, level=1):
    """Print function activation recursively"""
    text = wrap(
        "{0.line}: {0.name} ({0.start} - {0.finish})".format(activation),
        initial="  " * level)
    indent = text.index(": ") + 2
    print(text)
    activation.show(_print=lambda x, offset=0: print(
        wrap(x, initial=" " * (indent + offset))))

    for inner_activation in activation.children:
        print_function_activation(trial, inner_activation, level + 1)


def export_basic_info(trial: Trial, document: provo.ProvDocument) -> provo.ProvActivity:
    print_msg("Exporting basic trial information", True)
    return document.activity("trial{}".format(trial.id), trial.start, trial.finish,
                                      [(provo.PROV_TYPE, "trial"),
                                       ("codeHash", trial.code_hash),
                                       ("parentId", trial.parent_id),
                                       ("inheritedId", trial.inherited_id),
                                       ("command", trial.command)])

def export_prov(trial: Trial, args, name="provo", format="provn"):
    document = provo.ProvDocument()
    document.set_default_namespace("https://github.com/gems-uff/noworkflow")

    trialActivity = export_basic_info(trial, document)

    if args.modules:
        export_module_deps(trial, document)

    if args.function_defs:
        print_msg("this trial has the following functions:", True)
        print_trial_relationship(trial.function_defs)

    if args.environment:
        print_msg("this trial has been executed under the following"
                  " environment conditions", True)
        print_trial_relationship(trial.environment_attrs, breakline="\n",
                                 other="\n  ")

    if args.function_activations:
        print_msg("this trial has the following function activation "
                  "graphF:", True)
        for act in trial.initial_activations:  # pylint: disable=not-an-iterable
            print_function_activation(trial, act)

    if args.file_accesses:
        print_msg("this trial accessed the following files:", True)
        print_trial_relationship(trial.file_accesses)

    with open(name + "." + format, 'w') as file:
        document.serialize(destination=file, format=format)

    # e2 = document.entity('e2', [
    #    (provo.PROV_TYPE, "File"),
    #    ('path', "/shared/crime.txt"),
    #    ('creator', "Alice"),
    #    ('content', "There was a lot of crime in London last month"),
    # ])

    # a1 = document.activity('a1', datetime.datetime.now(), None, {provo.PROV_TYPE: "edit"})
    # References can be qnames or ProvRecord objects themselves
    # document.wasGeneratedBy(e2, a1, None, {'ex:fct': "save"})
    # document.wasAssociatedWith('a1', 'ag2', None, None, {provo.PROV_ROLE: "author"})
    # document.agent('ag2', {provo.PROV_TYPE: 'prov:Person', 'name': "Bob"})

