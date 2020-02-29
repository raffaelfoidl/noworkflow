from prov import model as provo

from noworkflow.now.persistence.models import Trial, Diff as DiffModel
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvDocument):
    print_msg("  Exporting basic trial information")
    _create_trial_info(document, trial)


def diff(diff: DiffModel, document: provo.ProvDocument):
    print_msg("  Exporting basic trial comparison information")
    _create_trial_info(document, diff.trial1, "_{}".format(diff.trial1.id))
    _create_trial_info(document, diff.trial2, "_{}".format(diff.trial2.id))

    document.wasInfluencedBy("trial{}Execution".format(diff.trial2.id),
                             "trial{}Execution".format(diff.trial1.id),
                             "trial{}ComparedTo{}".format(diff.trial2.id, diff.trial1.id),
                             [(provo.PROV_TYPE, "comparison")])


def _create_trial_info(document: provo.ProvDocument, trial: Trial, suffix=""):
    document.agent("{}{}".format(trial.script, suffix),
                   [(provo.PROV_TYPE, provo.PROV["SoftwareAgent"]),
                    ("codeHash", trial.code_hash),
                    ("script", trial.script),
                    ("id", trial.id)])

    document.activity("trial{}Execution".format(trial.id), trial.start, trial.finish,
                      [("nowCommand", trial.command),
                       ("parentId", trial.parent_id),
                       ("inheritedId", trial.inherited_id)])

    document.wasAssociatedWith("trial{}Execution".format(trial.id), "{}{}".format(trial.script, suffix), None,
                               "trial{}ExecutionByScript".format(trial.id))
