from noworkflow.now.persistence.models import Trial, Module
from noworkflow.now.utils.io import print_msg
import prov.model as provo


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting module dependencies")
    for module in trial.modules:  # type: Module
        document.entity("module{}".format(module.id),
                        [(provo.PROV_LABEL, module.name),
                         (provo.PROV_TYPE, "moduleDependency"),
                         ("version", module.version),
                         ("path", module.path),
                         ("codeHash", module.code_hash)])
