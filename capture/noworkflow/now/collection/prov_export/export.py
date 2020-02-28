import sys

import prov.model as provo
import prov.dot as provo_dot

from noworkflow.now.collection.prov_export import module_deps, function_defs, environment_attrs, \
    function_activations, file_accesses, basic_info
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
        function_defs.export(trial, bundle_def)

    if args.modules:
        bundle_dep = document.bundle("trial{}DeploymentProv".format(trial.id))
        module_deps.export(trial, bundle_dep)

    if args.environment:
        bundle_dep = document.bundle("trial{}DeploymentProv".format(trial.id)) if not bundle_dep else bundle_dep
        environment_attrs.export(trial, bundle_dep)

    if args.function_activations:
        bundle_exec = document.bundle("trial{}ExecutionProv".format(trial.id))
        function_activations.export(trial, bundle_exec)

    if args.file_accesses:
        bundle_exec = document.bundle("trial{}ExecutionProv".format(trial.id)) if not bundle_exec else bundle_exec
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

    _persist_document(document, args.filename, args.format, extension,
                      args.hideelemattr, args.hiderelattr, args.graphdir)


def _persist_document(document, name, format, extension, hide_elem_attr, hide_rel_attr, dir):
    print_msg("Persisting collected provenance to local storage")

    filename = "{}{}".format(name, extension)
    serializers = ["json", "rdf", "provn", "xml"]
    writers = ["raw", "dot", "jpeg", "png", "svg", "pdf", "plain"]

    if format in serializers:
        print_msg("  Employing serializer to export to {}".format(format))
        with open(filename, 'w') as file:
            document.serialize(destination=file, format=format)

    elif format in writers:
        print_msg("  Employing dot writer to export to {}".format(format))
        provo_dot.prov_to_dot(document, show_element_attributes=not hide_elem_attr, direction=dir,
                              show_relation_attributes=not hide_rel_attr).write(filename, format=format)

    else:
        print_msg("  Could not find suitable exporting module for {{name=\"{}\", format=\"{}\", extension=\"{}\"}}. "
                  "Try different input parameters.".format(name, format, extension))
        sys.exit(1)

    print_msg("Provenance export to file \"{}\" done.".format(filename), force=True)
