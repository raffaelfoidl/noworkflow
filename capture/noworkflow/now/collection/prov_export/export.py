import prov.model as provo
import prov.dot as provo_dot

from noworkflow.now.collection.prov_export import module_deps, function_defs, environment_attrs, \
    function_activations, file_accesses
from noworkflow.now.persistence.models import Trial
from noworkflow.now.utils.io import print_msg


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
