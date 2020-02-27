import itertools
from collections import Counter

import prov.model as provo
import prov.dot as provo_dot
import datetime

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


def export_module_deps(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting module dependencies", True)
    for module in trial.modules:  # type: Module
        document.entity("module{}".format(module.id),
                        [(provo.PROV_LABEL, module.name),
                         (provo.PROV_TYPE, "moduleDependency"),
                         ("version", module.version),
                         ("path", module.path),
                         ("codeHash", module.code_hash)])


def export_function_defs(trial: Trial, document: provo.ProvBundle):
    def function_definitions():
        document.activity("functionDefinition{}".format(function.id), None, None,
                          [(provo.PROV_LABEL, function.name),
                           (provo.PROV_TYPE, "functionDefinition"),
                           ("codeHash", function.code_hash),
                           ("firstLine", function.first_line),
                           ("lastLine", function.last_line),
                           ("docString", function.docstring.strip() if len(function.docstring.strip()) > 0 else None)])

    def argument_definitions():
        for arg in function.arguments:  # type: Object
            document.entity("argumentDefinition{}".format(arg.id),
                            [(provo.PROV_LABEL, arg.name),
                             (provo.PROV_TYPE, "argumentDefinition")])

    def argument_usage_definitions():
        for arg in function.arguments:  # type: Object
            document.used("functionDefinition{}".format(function.id),
                          "argumentDefinition{}".format(arg.id),
                          None,
                          "funcDef{}UsedArgDef{}".format(function.id, arg.id),
                          [(provo.PROV_ROLE, "argument"),
                           (provo.PROV_TYPE, "argumentDefinition")])

    def global_definitions():
        for glob in function.globals:  # type: Object
            document.entity("globalDefinition{}".format(glob.id),
                            [(provo.PROV_LABEL, glob.name),
                             (provo.PROV_TYPE, "globalDefinition")])

    def global_usage_definitions():
        for glob in function.globals:  # type: Object
            document.used("functionDefinition{}".format(function.id),
                          "globalDefinition{}".format(glob.id),
                          None,
                          "funcDef{}UsedGlobalDef{}".format(function.id, glob.id),
                          [(provo.PROV_ROLE, "global"),
                           (provo.PROV_TYPE, "globalDefinition")])

    def call_definitions():
        for call in function.function_calls:  # type: Object
            document.activity("callDefinition{}".format(call.id), None, None,
                              [(provo.PROV_LABEL, call.name),
                               (provo.PROV_TYPE, "callDefinition")])

    def call_usage_definitions():
        for call in function.function_calls:  # type: Object
            document.wasInformedBy("callDefinition{}".format(call.id),
                                   "functionDefinition{}".format(function.id),
                                   "funcDef{}CalledBy{}".format(function.id, call.id),
                                   [(provo.PROV_ROLE, "call"),
                                    (provo.PROV_TYPE, "callDefinition")])

    print_msg("Exporting function definitions", True)
    for function in trial.function_defs:  # type: FunctionDef
        function_definitions()

        argument_definitions()
        argument_usage_definitions()

        global_definitions()
        global_usage_definitions()

        call_definitions()
        call_usage_definitions()


def export_environment_attrs(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting environment conditions", True)

    collection = document.collection("environmentAttributes")

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        document.entity("environmentAttribute{}".format(env_attr.id),
                        [(provo.PROV_LABEL, env_attr.name),
                         (provo.PROV_VALUE, env_attr.value),
                         (provo.PROV_TYPE, "environmentAttribute")])

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        collection.hadMember("environmentAttribute{}".format(env_attr.id))

    print_trial_relationship(trial.environment_attrs, breakline="\n", other="\n  ")


def export_file_accesses(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting file accesses", True)

    for f_access in trial.file_accesses:  # type: FileAccess
        document.activity("fileAccess{}".format(f_access.id), None, None,
                          [(provo.PROV_LOCATION, f_access.name),
                           (provo.PROV_TYPE, f_access.mode),
                           (provo.PROV_ATTR_TIME, f_access.timestamp),
                           ("buffering", f_access.buffering),
                           ("functionActivationId", f_access.function_activation_id),  # Todo match
                           ("caller", f_access.caller),  # todo match
                           ("contentHashBefore", f_access.content_hash_before),
                           ("contentHashAfter", f_access.content_hash_after)])

    print_trial_relationship(trial.file_accesses)


def export_function_activations(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting function activations", True)
    for act in trial.initial_activations:  # type: Activation
        export_function_activation(trial, act, document)


def export_function_activation(trial: Trial, activation: Activation, document: provo.ProvBundle, level: int = 1):
    """Print function activation recursively"""
    text = wrap(
        "{0.line}: {0.name} ({0.start} - {0.finish})".format(activation),
        initial="  " * level)
    indent = text.index(": ") + 2
    print(text)
    activation.show(_print=lambda x, offset=0: print(
        wrap(x, initial=" " * (indent + offset))))

    document.activity("functionActivation{}".format(activation.id),
                      activation.start,
                      activation.finish,
                      [(provo.PROV_LABEL, activation.name),
                       (provo.PROV_TYPE, "functionActivation"),
                       ("line", activation.line),
                       ("caller", "functionActivation{}".format(activation.caller_id)) if
                       activation.caller_id is not None else (None, None)])

    if activation.caller_id is not None:
        document.wasInformedBy("functionActivation{}".format(activation.id),
                               "functionActivation{}".format(activation.caller_id),
                               "funcAct{}CalledBy{}".format(activation.id, activation.caller_id))

    args = list(activation.arguments)
    if args:
        for arg in args:  # type: ObjectValue
            document.entity("argumentActivation{}".format(arg.id),
                            [(provo.PROV_LABEL, arg.name),
                             (provo.PROV_VALUE, arg.value),
                             (provo.PROV_TYPE, "argumentActivation")])

            document.used("functionActivation{}".format(arg.function_activation_id),
                          "argumentActivation{}".format(arg.id),
                          activation.start,
                          "funcAct{}UsedArgAct{}".format(activation.id, arg.id),
                          [(provo.PROV_ROLE, "argument"),
                           (provo.PROV_TYPE, "argumentActivation")])

    globs = list(activation.globals)
    if globs:
        for glob in globs:  # type: ObjectValue
            document.entity("globalActivation{}".format(glob.id),
                            [(provo.PROV_LABEL, glob.name),
                             (provo.PROV_VALUE, glob.value),
                             (provo.PROV_TYPE, "globalActivation")])

            document.used("functionActivation{}".format(glob.function_activation_id),
                          "globalActivation{}".format(glob.id),
                          activation.start,
                          "funcAct{}UsedGlobalAct{}".format(activation.id, glob.id),
                          [(provo.PROV_ROLE, "global"),
                           (provo.PROV_TYPE, "globalActivation")])

    if activation.return_value is not None and activation.return_value != "None":
        document.entity("funcAct{}ReturnValue".format(activation.id),
                        [(provo.PROV_VALUE, activation.return_value),
                         (provo.PROV_TYPE, "returnValue")])

        document.wasGeneratedBy("funcAct{}ReturnValue".format(activation.id),
                                "functionActivation{}".format(activation.id),
                                activation.finish,
                                "funcAct{}RetValGeneration".format(activation.id))

    if len(list(activation.variables)) > 0:
        print("#: " + list(activation.variables)[0].name)

    for inner_activation in activation.children:
        export_function_activation(trial, inner_activation, document, level + 1)


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
        export_module_deps(trial, document.bundle("trial{}ModuleDependencies".format(trial.id)))

    if args.function_defs:
        export_function_defs(trial, document.bundle("trial{}FunctionDefinitions".format(trial.id)))

    if args.environment:
        export_environment_attrs(trial, document.bundle("trial{}Environment".format(trial.id)))

    if args.function_activations:
        export_function_activations(trial, document.bundle("trial{}FunctionActivations".format(trial.id)))

    if args.file_accesses:
        export_file_accesses(trial, document.bundle("trial{}FileAccesses".format(trial.id)))

    with open(name + "." + format, 'w') as file:
        document.serialize(destination=file, format=format)
        provo_dot.prov_to_dot(document).write_pdf(name + ".pdf")
