import prov.model as provo
import prov.dot as provo_dot

from noworkflow.now.collection.prov_export.basic_info import create_trial_info
from noworkflow.now.collection.prov_export.environment_attrs import create_env_attr
from noworkflow.now.collection.prov_export.file_accesses import create_file_access
from noworkflow.now.collection.prov_export.module_deps import create_module_dep
from noworkflow.now.persistence.models import Trial, Module, EnvironmentAttr, FileAccess
from noworkflow.now.persistence.models.diff import Diff as DiffModel
from noworkflow.now.utils.io import print_msg


def module_changes(diff: DiffModel, document: provo.ProvDocument):
    added, removed, replaced = diff.modules

    for module in added:  # type: Module
        create_module_dep(module, document)
        document.wasGeneratedBy("module{}".format(module.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "module{}AddDep".format(module.id),
                                [(provo.PROV_ROLE, "dependencyAddition")])

    for module in removed:  # type: Module
        create_module_dep(module, document)
        document.wasInvalidatedBy("module{}".format(module.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "module{}RemoveDep".format(module.id),
                                  [(provo.PROV_ROLE, "dependencyRemoval")])

    for (mod_removed, mod_added) in replaced:  # type: Module
        create_module_dep(mod_added, document, suffix="_a")
        document.wasGeneratedBy("module{}_a".format(mod_added.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "module{}AddDep".format(mod_added.id),
                                [(provo.PROV_ROLE, "dependencyAddition")])

        create_module_dep(mod_removed, document, suffix="_r")
        document.wasInvalidatedBy("module{}_r".format(mod_removed.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "module{}RemoveDep".format(mod_removed.id),
                                  [(provo.PROV_ROLE, "dependencyRemoval")])

        document.wasRevisionOf("module{}_a".format(mod_added.id),
                               "module{}_r".format(mod_removed.id),
                               "trial{}Execution".format(diff.trial2.id), None, None, None,
                               [(provo.PROV_ROLE, "dependencyReplacement")])


def environment_attr_changes(diff: DiffModel, document: provo.ProvDocument):
    added, removed, replaced = diff.environment

    for env_attr in added:  # type: EnvironmentAttr
        create_env_attr(document, env_attr)
        document.wasGeneratedBy("environmentAttribute{}".format(env_attr.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "environmentAttribute{}AddAttr".format(env_attr.id),
                                [(provo.PROV_ROLE, "environmentAttributeAddition")])

    for env_attr in removed:  # type: EnvironmentAttr
        create_env_attr(document, env_attr)
        document.wasInvalidatedBy("environmentAttribute{}".format(env_attr.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "environmentAttribute{}RemoveAttr".format(env_attr.id),
                                  [(provo.PROV_ROLE, "environmentAttributeRemoval")])

    for (attr_removed, attr_added) in replaced:  # type: EnvironmentAttr
        create_env_attr(document, attr_added, suffix="_a")
        document.wasGeneratedBy("environmentAttribute{}_a".format(attr_added.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "environmentAttribute{}AddAttr".format(attr_added.id),
                                [(provo.PROV_ROLE, "environmentAttributeAddition")])

        create_env_attr(document, attr_removed, suffix="_r")
        document.wasInvalidatedBy("environmentAttribute{}_r".format(attr_removed.id),
                                  "trial{}Execution".format(diff.trial2.id), None,
                                  "environmentAttribute{}RemoveAttr".format(attr_removed.id),
                                  [(provo.PROV_ROLE, "environmentAttributeRemoval")])

        document.wasRevisionOf("environmentAttribute{}_a".format(attr_added.id),
                               "environmentAttribute{}_r".format(attr_removed.id),
                               "trial{}Execution".format(diff.trial2.id), None, None, None,
                               [(provo.PROV_ROLE, "environmentAttributeReplacement")])


def file_access_changes(diff: DiffModel, document: provo.ProvDocument):
    added, removed, replaced = diff.file_accesses

    for f_access in added:  # type: FileAccess
        create_file_access(document, f_access, suffix="_a")
        document.wasInformedBy("fileAccess{}_a".format(f_access.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}AddAcc".format(f_access.id),
                               [(provo.PROV_TYPE, "fileAccessAddition")])

    for f_access in removed:  # type: FileAccess
        create_file_access(document, f_access, suffix="_r")
        document.wasInformedBy("fileAccess{}_r".format(f_access.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}RemoveAcc".format(f_access.id),
                               [(provo.PROV_TYPE, "fileAccessRemoval")])

    for (f_removed, f_added) in replaced:  # type: FileAccess
        create_file_access(document, f_added, suffix="_a")
        document.wasInformedBy("fileAccess{}_a".format(f_added.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}AddAcc".format(f_added.id),
                               [(provo.PROV_TYPE, "fileAccessAddition")])

        create_file_access(document, f_removed, suffix="_r")
        document.wasInformedBy("fileAccess{}_r".format(f_removed.id),
                               "trial{}Execution".format(diff.trial2.id),
                               "fileAcc{}RemoveAcc".format(f_removed.id),
                               [(provo.PROV_TYPE, "fileAccessRemoval")])

        document.wasInformedBy("fileAccess{}_a".format(f_added.id),
                               "fileAccess{}_r".format(f_removed.id),
                               "fileAcc{}ReplacesAcc{}".format(f_added.id, f_removed.id),
                               [(provo.PROV_TYPE, "fileAccessReplacement")])


def export_diff(diff: DiffModel, args):
    document = provo.ProvDocument()
    document.set_default_namespace(args.defaultns)

    print_msg("Exporting comparison provenance of trials {} and {} in PROV-O format"
              .format(diff.trial1.id, diff.trial2.id), force=True)

    basic_info(diff, document)

    if args.modules:
        module_changes(diff, document)

    if args.environment:
        environment_attr_changes(diff, document)

    if args.file_accesses:
        file_access_changes(diff, document)

    with open("hello.pn", "w") as file:
        document.serialize(destination=file, format="provn")
    provo_dot.prov_to_dot(document).write("hello.pdf", format="pdf")


def basic_info(diff: DiffModel, document: provo.ProvDocument):
    trial_info(diff.trial1, document)
    trial_info(diff.trial2, document)

    document.wasInfluencedBy("trial{}Execution".format(diff.trial2.id),
                             "trial{}Execution".format(diff.trial1.id),
                             "trial{}ComparedTo{}".format(diff.trial2.id, diff.trial1.id),
                             [(provo.PROV_TYPE, "comparison")])


def trial_info(trial: Trial, document: provo.ProvDocument):
    create_trial_info(document, trial, "_{}".format(trial.id))
