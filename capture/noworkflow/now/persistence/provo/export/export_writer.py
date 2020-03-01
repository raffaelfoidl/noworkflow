import prov.model as provo

from noworkflow.now.persistence.provo.common.file_writer import persist_document
from noworkflow.now.persistence.provo.export import function_activations, function_defs
from noworkflow.now.persistence.provo.common import environment_attrs, file_accesses, module_deps, basic_info
from noworkflow.now.persistence.models import Trial
from noworkflow.now.utils.io import print_msg


def export_provo(trial: Trial, args, extension):
    document = provo.ProvDocument()
    document.set_default_namespace(args.defaultns)
    bundle_def = None
    bundle_dep = None
    bundle_exec = None

    print_msg("Exporting provenance of trial {} in PROV-O format".format(trial.id), force=True)
    document.collection("trial{}Prov".format(trial.id), [(provo.PROV_LABEL, "provenance collected by noworfklow")])
    basic_info.export(trial, document)

    if args.function_defs:
        bundle_def = document.bundle("trial{}DefinitionProv".format(trial.id)) if not bundle_def else bundle_def
        bundle_def.set_default_namespace(args.defaultns)
        function_defs.export(trial, bundle_def)

    if args.modules:
        bundle_dep = document.bundle("trial{}DeploymentProv".format(trial.id))
        bundle_dep.set_default_namespace(args.defaultns)
        module_deps.export(trial, bundle_dep)

    if args.environment:
        bundle_dep = document.bundle("trial{}DeploymentProv".format(trial.id)) if not bundle_dep else bundle_dep
        bundle_dep.set_default_namespace(args.defaultns)
        environment_attrs.export(trial, bundle_dep)

    if args.function_activations:
        bundle_exec = document.bundle("trial{}ExecutionProv".format(trial.id))
        bundle_exec.set_default_namespace(args.defaultns)
        function_activations.export(trial, bundle_exec, args.recursion_depth)

    if args.file_accesses:
        bundle_exec = document.bundle("trial{}ExecutionProv".format(trial.id)) if not bundle_exec else bundle_exec
        bundle_exec.set_default_namespace(args.defaultns)
        file_accesses.export(trial, bundle_exec)

    if bundle_def:
        document.hadMember("trial{}Prov".format(trial.id), bundle_def.identifier)
        document.wasGeneratedBy(bundle_def.identifier, "trial{}Execution".format(trial.id), None)
    if bundle_dep:
        document.hadMember("trial{}Prov".format(trial.id), bundle_dep.identifier)
        document.wasGeneratedBy(bundle_dep.identifier, "trial{}Execution".format(trial.id), None)
    if bundle_exec:
        document.hadMember("trial{}Prov".format(trial.id), bundle_exec.identifier)
        document.wasGeneratedBy(bundle_exec.identifier, "trial{}Execution".format(trial.id), None)

    persist_document(document, args.file, args.format, extension,
                     args.hide_elem_attr, args.hide_rel_attr, args.graph_dir)
