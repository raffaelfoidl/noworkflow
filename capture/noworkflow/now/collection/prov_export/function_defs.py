import prov.model as provo

from noworkflow.now.persistence.models import Trial, Object, FunctionDef
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting function definitions")
    for function in trial.function_defs:  # type: FunctionDef
        _function_definitions(document, function)

        _argument_definitions(function, document)
        _argument_usage_definitions(function, document)

        _global_definitions(function, document)
        _global_usage_definitions(function, document)

        _call_definitions(function, document)
        _call_usage_definitions(function, document)


def _call_usage_definitions(function, document):
    for call in function.function_calls:  # type: Object
        document.wasInformedBy("callDefinition{}".format(call.id),
                               "functionDefinition{}".format(function.id),
                               "callDef{}CalledByFuncDef{}".format(call.id, function.id),
                               [(provo.PROV_TYPE, "callDefinition")])


def _call_definitions(function, document):
    for call in function.function_calls:  # type: Object
        document.activity("callDefinition{}".format(call.id), None, None,
                          [(provo.PROV_LABEL, call.name),
                           (provo.PROV_TYPE, "callDefinition")])


def _global_usage_definitions(function, document):
    for glob in function.globals:  # type: Object
        document.used("functionDefinition{}".format(function.id),
                      "globalDefinition{}".format(glob.id),
                      None,
                      "funcDef{}UsedGlobalDef{}".format(function.id, glob.id),
                      [(provo.PROV_ROLE, "global"),
                       (provo.PROV_TYPE, "globalDefinition")])


def _global_definitions(function, document):
    for glob in function.globals:  # type: Object
        document.entity("globalDefinition{}".format(glob.id),
                        [(provo.PROV_LABEL, glob.name),
                         (provo.PROV_TYPE, "globalDefinition")])


def _argument_usage_definitions(function, document):
    for arg in function.arguments:  # type: Object
        document.used("functionDefinition{}".format(function.id),
                      "argumentDefinition{}".format(arg.id),
                      None,
                      "funcDef{}UsedArgDef{}".format(function.id, arg.id),
                      [(provo.PROV_ROLE, "argument"),
                       (provo.PROV_TYPE, "argumentDefinition")])


def _argument_definitions(function, document):
    for arg in function.arguments:  # type: Object
        document.entity("argumentDefinition{}".format(arg.id),
                        [(provo.PROV_LABEL, arg.name),
                         (provo.PROV_TYPE, "argumentDefinition")])


def _function_definitions(document, function):
    doc_string = function.docstring.strip()[:150].replace("\n", " ") + \
                 ('...' if len(function.docstring.strip()) > 150 else '')

    document.activity("functionDefinition{}".format(function.id), None, None,
                      [(provo.PROV_LABEL, function.name),
                       (provo.PROV_TYPE, "functionDefinition"),
                       ("codeHash", function.code_hash),
                       ("firstLine", function.first_line),
                       ("lastLine", function.last_line),
                       ("docString", doc_string if len(function.docstring.strip()) > 0 else None)])
