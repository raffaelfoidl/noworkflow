import itertools
from collections import Counter

import prov.model as provo
import prov.dot as provo_dot
import datetime

from noworkflow.now.collection.prov_export import module_deps, function_defs, environment_attrs, \
    function_activations, file_accesses
from noworkflow.now.persistence.models import Trial, Module, FunctionDef, Object, EnvironmentAttr, FileAccess, \
    Activation, ObjectValue
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







def export_basic_info(trial: Trial, document: provo.ProvDocument):
    print_msg("Exporting basic trial information", True)
    document.bundle("trial{}".format(trial.id))

    document.entity("trial{}Info".format(trial.id),
                    [(provo.PROV_TYPE, "trial"),
                     (provo.PROV_ATTR_STARTTIME, trial.start),
                     (provo.PROV_ATTR_ENDTIME, trial.finish),
                     ("codeHash", trial.code_hash),
                     ("parentId", trial.parent_id),
                     ("inheritedId", trial.inherited_id),
                     ("command", trial.command)])


def export_prov(trial: Trial, args, name="provo", format="provn"):
    document = provo.ProvDocument()
    document.set_default_namespace("https://github.com/gems-uff/noworkflow")

    export_basic_info(trial, document)

    if args.modules:
        module_deps.export(trial, document.bundle("trial{}ModuleDependencies".format(trial.id)))

    if args.function_defs:
        function_defs.export(trial, document.bundle("trial{}FunctionDefinitions".format(trial.id)))

    if args.environment:
        environment_attrs.export(trial, document.bundle("trial{}Environment".format(trial.id)))

    if args.function_activations:
        function_activations.export(trial, document.bundle("trial{}FunctionActivations".format(trial.id)))

    if args.file_accesses:
        file_accesses.export(trial, document.bundle("trial{}FileAccesses".format(trial.id)))

    with open(name + "." + format, 'w') as file:
        document.serialize(destination=file, format=format)
        provo_dot.prov_to_dot(document).write_pdf(name + ".pdf")
