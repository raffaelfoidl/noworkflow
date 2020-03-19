import prov.model as provo

from noworkflow.now.persistence.models.diff import Diff as DiffModel
from noworkflow.now.persistence.provo.common import basic_info, module_deps, environment_attrs, file_accesses
from noworkflow.now.persistence.provo.common.file_writer import persist_document
from noworkflow.now.utils.io import print_msg


def export_diff(diff: DiffModel, args, extension):
    document = provo.ProvDocument()
    document.set_default_namespace(args.defaultns)

    print_msg("Exporting comparison provenance of trials {} and {} in PROV-O format"
              .format(diff.trial1.id, diff.trial2.id), force=True)

    basic_info.diff(diff, document)

    if args.modules:
        module_deps.diff(diff, document)

    if args.environment:
        environment_attrs.diff(diff, document)

    if args.file_accesses:
        file_accesses.diff(diff, document)

    persist_document(document, args.file, args.format, extension,
                     args.hide_elem_attr, args.hide_rel_attr, args.graph_dir)

