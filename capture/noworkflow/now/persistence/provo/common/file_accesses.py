from prov import model as provo

from noworkflow.now.persistence.models import Trial, FileAccess, Diff as DiffModel
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("  Exporting file accesses")

    for f_access in trial.file_accesses:  # type: FileAccess
        _create_file_access(document, f_access)

        if document.get_record("functionActivation{}".format(f_access.function_activation_id)):
            document.wasInformedBy("fileAccess{}".format(f_access.id),
                                   "functionActivation{}".format(f_access.function_activation_id),
                                   "fileAcc{}ByFuncAct{}".format(f_access.id, f_access.function_activation_id),
                                   [(provo.PROV_TYPE, "fileAccess")])


def diff(diff: DiffModel, document: provo.ProvDocument):
    print_msg("  Exporting file accesses comparison")
    added, removed, replaced = diff.file_accesses

    for f_access in added:  # type: FileAccess
        _create_file_access(document, f_access, suffix="_a")
        document.wasInformedBy("fileAccess{}_a".format(f_access.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}AddAcc".format(f_access.id),
                               [(provo.PROV_TYPE, "fileAccessAddition")])

    for f_access in removed:  # type: FileAccess
        _create_file_access(document, f_access, suffix="_r")
        document.wasInformedBy("fileAccess{}_r".format(f_access.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}RemoveAcc".format(f_access.id),
                               [(provo.PROV_TYPE, "fileAccessRemoval")])

    for (f_removed, f_added) in replaced:  # type: FileAccess
        _create_file_access(document, f_added, suffix="_a")
        document.wasInformedBy("fileAccess{}_a".format(f_added.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}AddAcc".format(f_added.id),
                               [(provo.PROV_TYPE, "fileAccessAddition")])

        _create_file_access(document, f_removed, suffix="_r")
        document.wasInformedBy("fileAccess{}_r".format(f_removed.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}RemoveAcc".format(f_removed.id),
                               [(provo.PROV_TYPE, "fileAccessRemoval")])

        document.wasInformedBy("fileAccess{}_a".format(f_added.id),
                               "fileAccess{}_r".format(f_removed.id),
                               "fileAcc{}ReplacesAcc{}".format(f_added.id, f_removed.id),
                               [(provo.PROV_TYPE, "fileAccessReplacement")])


def _create_file_access(document: provo.ProvBundle, f_access: FileAccess, suffix=""):
    document.activity("fileAccess{}{}".format(f_access.id, suffix), None, None,
                      [(provo.PROV_LOCATION, f_access.name),
                       (provo.PROV_TYPE, f_access.mode),
                       (provo.PROV_ATTR_TIME, f_access.timestamp),
                       ("buffering", f_access.buffering),
                       ("contentHashBefore", f_access.content_hash_before),
                       ("contentHashAfter", f_access.content_hash_after),
                       ("id", f_access.id) if suffix else (None, None)])
