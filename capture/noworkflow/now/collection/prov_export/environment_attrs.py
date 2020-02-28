import prov.model as provo

from noworkflow.now.persistence.models import Trial, EnvironmentAttr
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting environment conditions")

    collection = document.collection("environmentAttributes")

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        document.entity("environmentAttribute{}".format(env_attr.id),
                        [(provo.PROV_LABEL, env_attr.name),
                         (provo.PROV_VALUE, env_attr.value[:150] + ('..' if len(env_attr.value) > 150 else '')),
                         (provo.PROV_TYPE, "environmentAttribute")])

    for env_attr in trial.environment_attrs:  # type: EnvironmentAttr
        collection.hadMember("environmentAttribute{}".format(env_attr.id))
