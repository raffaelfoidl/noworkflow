import prov.model as provo
import prov.dot as provo_dot

from noworkflow.now.collection.prov_export.module_deps import create_module_dep
from noworkflow.now.persistence.models import Trial, Module
from noworkflow.now.persistence.models.diff import Diff as DiffModel
from noworkflow.now.utils.functions import truncate
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

    for module in replaced:  # type: Module
        create_module_dep(module, document)
        document.wasGeneratedBy("module{}".format(module.id),
                                "trial{}Execution".format(diff.trial2.id), None,
                                "module{}ReplaceDep".format(module.id),
                                [(provo.PROV_ROLE, "dependencyReplacement")])


def export_diff(diff: DiffModel, args):
    document = provo.ProvDocument()
    document.set_default_namespace(args.defaultns)

    print_msg("Exporting comparison provenance of trials {} and {} in PROV-O format"
              .format(diff.trial1.id, diff.trial2.id), force=True)

    basic_info(diff, document)

    if args.modules:
        module_changes(diff, document)

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
    document.agent("{}_{}".format(trial.script, trial.id),
                   [(provo.PROV_TYPE, provo.PROV["SoftwareAgent"]),
                    ("codeHash", trial.code_hash),
                    ("script", trial.script),
                    ("id", trial.id)])

    document.activity("trial{}Execution".format(trial.id), trial.start, trial.finish,
                      [("nowCommand", trial.command),
                       ("parentId", trial.parent_id),
                       ("inheritedId", trial.inherited_id)])

    document.wasAssociatedWith("trial{}Execution".format(trial.id),
                               "{}_{}".format(trial.script, trial.id), None,
                               "trial{}ExecutionByScript".format(trial.id))
