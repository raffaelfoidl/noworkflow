import prov.model as provo

from noworkflow.now.persistence.models import Trial, Activation, ObjectValue
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle, max_depth: int):
    print_msg("Exporting function activations")

    for act in trial.initial_activations:  # type: Activation
        export_function_activation(trial, act, document, max_depth=max_depth, level=1)


def export_function_activation(trial: Trial, activation: Activation, document: provo.ProvBundle, max_depth: int,
                               level: int = 1):
    _function_activation(activation, document, level)
    _function_parent(activation, document)
    _argument_activation(activation, document)
    _global_activation(activation, document)
    _return_value(activation, document)

    if max_depth == 0 or level < max_depth:
        # Print function activations recursively
        for inner_activation in activation.children:
            export_function_activation(trial, inner_activation, document, max_depth, level + 1)


def _return_value(activation, document):
    if activation.return_value is not None and activation.return_value != "None":
        document.entity("funcAct{}ReturnValue".format(activation.id),
                        [(provo.PROV_VALUE,
                          activation.return_value[:150] + ('...' if len(activation.return_value) > 150 else '')),
                         (provo.PROV_TYPE, "returnValue")])

        document.wasGeneratedBy("funcAct{}ReturnValue".format(activation.id),
                                "functionActivation{}".format(activation.id),
                                activation.finish,
                                "funcAct{}RetValGeneration".format(activation.id))


def _global_activation(activation, document):
    globs = list(activation.globals)
    if globs:
        for glob in globs:  # type: ObjectValue
            document.entity("globalActivation{}".format(glob.id),
                            [(provo.PROV_LABEL, glob.name),
                             (provo.PROV_VALUE, glob.value[:150] + ('...' if len(glob.value) > 150 else '')),
                             (provo.PROV_TYPE, "globalActivation")])

            document.used("functionActivation{}".format(glob.function_activation_id),
                          "globalActivation{}".format(glob.id),
                          activation.start,
                          "funcAct{}UsedGlobalAct{}".format(activation.id, glob.id),
                          [(provo.PROV_ROLE, "global"),
                           (provo.PROV_TYPE, "globalActivation")])


def _argument_activation(activation, document):
    args = list(activation.arguments)
    if args:
        for arg in args:  # type: ObjectValue
            document.entity("argumentActivation{}".format(arg.id),
                            [(provo.PROV_LABEL, arg.name),
                             (provo.PROV_VALUE, arg.value[:150] + ('...' if len(arg.value) > 150 else '')),
                             (provo.PROV_TYPE, "argumentActivation")])

            document.used("functionActivation{}".format(arg.function_activation_id),
                          "argumentActivation{}".format(arg.id),
                          activation.start,
                          "funcAct{}UsedArgAct{}".format(activation.id, arg.id),
                          [(provo.PROV_ROLE, "argument"),
                           (provo.PROV_TYPE, "argumentActivation")])


def _function_parent(activation: Activation, document):
    if activation.caller_id is not None:
        document.wasInformedBy("functionActivation{}".format(activation.id),
                               "functionActivation{}".format(activation.caller_id),
                               "funcAct{}CalledBy{}".format(activation.id, activation.caller_id),
                               [(provo.PROV_TYPE, "callActivation")])


def _function_activation(activation: Activation, document, depth):
    document.activity("functionActivation{}".format(activation.id),
                      activation.start,
                      activation.finish,
                      [(provo.PROV_LABEL, activation.name),
                       (provo.PROV_TYPE, "functionActivation"),
                       ("line", activation.line),
                       ("depth", depth)])
