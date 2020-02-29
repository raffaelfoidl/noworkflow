import prov.model as provo
from noworkflow.now.persistence.models import Trial
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvDocument):
    print_msg("Exporting basic trial information")
    create_trial_info(document, trial)


def create_trial_info(document: provo.ProvDocument, trial: Trial, suffix=""):
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
