from noworkflow.now.persistence.models import Trial, Module
from noworkflow.now.utils.functions import truncate
from noworkflow.now.utils.io import print_msg
import prov.model as provo


def create_module_dep(module: Module, document: provo.ProvBundle, suffix=""):
    document.entity("module{}{}".format(module.id, suffix),
                    [(provo.PROV_LABEL, module.name),
                     (provo.PROV_TYPE, "moduleDependency"),
                     ("version", module.version),
                     (provo.PROV_LOCATION, truncate(module.path)),
                     ("codeHash", module.code_hash)])


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting module dependencies")

    collection = document.collection("moduleDependencies")

    for module in trial.modules:  # type: Module
        create_module_dep(module, document)

    for module in trial.modules:  # type: Module
        collection.hadMember("module{}".format(module.id))
