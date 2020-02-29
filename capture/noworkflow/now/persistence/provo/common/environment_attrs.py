from prov import model as provo

from noworkflow.now.persistence.models import Trial, EnvironmentAttr, Diff as DiffModel
from noworkflow.now.utils.functions import truncate
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting environment conditions")

    collection = document.collection("environmentAttributes")

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        _create_env_attr(document, env_attr)

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        collection.hadMember("environmentAttribute{}".format(env_attr.id))


def diff(diff: DiffModel, document: provo.ProvDocument):
    added, removed, replaced = diff.environment

    for env_attr in added:  # type: EnvironmentAttr
        _create_env_attr(document, env_attr)
        document.wasGeneratedBy("environmentAttribute{}".format(env_attr.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "environmentAttribute{}AddAttr".format(env_attr.id),
                                [(provo.PROV_ROLE, "environmentAttributeAddition")])

    for env_attr in removed:  # type: EnvironmentAttr
        _create_env_attr(document, env_attr)
        document.wasInvalidatedBy("environmentAttribute{}".format(env_attr.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "environmentAttribute{}RemoveAttr".format(env_attr.id),
                                  [(provo.PROV_ROLE, "environmentAttributeRemoval")])

    for (attr_removed, attr_added) in replaced:  # type: EnvironmentAttr
        _create_env_attr(document, attr_added, suffix="_a")
        document.wasGeneratedBy("environmentAttribute{}_a".format(attr_added.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "environmentAttribute{}AddAttr".format(attr_added.id),
                                [(provo.PROV_ROLE, "environmentAttributeAddition")])

        _create_env_attr(document, attr_removed, suffix="_r")
        document.wasInvalidatedBy("environmentAttribute{}_r".format(attr_removed.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "environmentAttribute{}RemoveAttr".format(attr_removed.id),
                                  [(provo.PROV_ROLE, "environmentAttributeRemoval")])

        document.wasRevisionOf("environmentAttribute{}_a".format(attr_added.id),
                               "environmentAttribute{}_r".format(attr_removed.id),
                               "trial{}Execution".format(diff.trial2.id), None, None, None,
                               [(provo.PROV_ROLE, "environmentAttributeReplacement")])


def _create_env_attr(document: provo.ProvBundle, env_attr: EnvironmentAttr, suffix=""):
    document.entity("environmentAttribute{}{}".format(env_attr.id, suffix),
                    [(provo.PROV_LABEL, env_attr.name),
                     (provo.PROV_VALUE, truncate(env_attr.value)),
                     (provo.PROV_TYPE, "environmentAttribute"),
                     ("id", env_attr.id) if suffix else (None, None)])
