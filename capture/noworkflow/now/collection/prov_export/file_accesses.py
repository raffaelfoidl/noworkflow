import prov.model as provo

from noworkflow.now.persistence.models import Trial, FileAccess
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting file accesses")

    for f_access in trial.file_accesses:  # type: FileAccess
        document.activity("fileAccess{}".format(f_access.id), None, None,
                          [(provo.PROV_LOCATION, f_access.name),
                           (provo.PROV_TYPE, f_access.mode),
                           (provo.PROV_ATTR_TIME, f_access.timestamp),
                           ("buffering", f_access.buffering),
                           ("contentHashBefore", f_access.content_hash_before),
                           ("contentHashAfter", f_access.content_hash_after)])

        if document.get_record("functionActivation{}".format(f_access.function_activation_id)):
            document.wasInformedBy("fileAccess{}".format(f_access.id),
                                   "functionActivation{}".format(f_access.function_activation_id),
                                   "fileAcc{}ByFuncAct{}".format(f_access.id, f_access.function_activation_id),
                                   [(provo.PROV_TYPE, "fileAccess")])
