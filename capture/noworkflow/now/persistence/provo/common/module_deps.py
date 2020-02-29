from prov import model as provo

from noworkflow.now.persistence.models import Trial, Module, Diff as DiffModel
from noworkflow.now.utils.functions import truncate
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvBundle):
    print_msg("Exporting module dependencies")

    collection = document.collection("moduleDependencies")

    for module in trial.modules:  # type: Module
        _create_module_dep(module, document)

    for module in trial.modules:  # type: Module
        collection.hadMember("module{}".format(module.id))


def diff(diff: DiffModel, document: provo.ProvDocument):
    added, removed, replaced = diff.modules

    for module in added:  # type: Module
        _create_module_dep(module, document)
        document.wasGeneratedBy("module{}".format(module.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "module{}AddDep".format(module.id),
                                [(provo.PROV_ROLE, "dependencyAddition")])

    for module in removed:  # type: Module
        _create_module_dep(module, document)
        document.wasInvalidatedBy("module{}".format(module.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "module{}RemoveDep".format(module.id),
                                  [(provo.PROV_ROLE, "dependencyRemoval")])

    for (mod_removed, mod_added) in replaced:  # type: Module
        _create_module_dep(mod_added, document, suffix="_a")
        document.wasGeneratedBy("module{}_a".format(mod_added.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "module{}AddDep".format(mod_added.id),
                                [(provo.PROV_ROLE, "dependencyAddition")])

        _create_module_dep(mod_removed, document, suffix="_r")
        document.wasInvalidatedBy("module{}_r".format(mod_removed.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "module{}RemoveDep".format(mod_removed.id),
                                  [(provo.PROV_ROLE, "dependencyRemoval")])

        document.wasRevisionOf("module{}_a".format(mod_added.id),
                               "module{}_r".format(mod_removed.id),
                               "trial{}Execution".format(diff.trial2.id), None, None, None,
                               [(provo.PROV_ROLE, "dependencyReplacement")])


def _create_module_dep(module: Module, document: provo.ProvBundle, suffix=""):
    document.entity("module{}{}".format(module.id, suffix),
                    [(provo.PROV_LABEL, module.name),
                     (provo.PROV_TYPE, "moduleDependency"),
                     ("version", module.version),
                     (provo.PROV_LOCATION, truncate(module.path)),
                     ("codeHash", module.code_hash),
                     ("id", module.id) if suffix else (None, None)])
