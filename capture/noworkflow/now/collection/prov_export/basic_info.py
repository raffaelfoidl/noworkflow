import prov.model as provo
from noworkflow.now.persistence.models import Trial
from noworkflow.now.utils.io import print_msg


def export(trial: Trial, document: provo.ProvDocument):
    print_msg("Exporting basic trial information")

    document.agent(trial.script,
                   [(provo.PROV_TYPE, provo.PROV["SoftwareAgent"]),
                    ("codeHash", trial.code_hash),
                    ("id", trial.id)])

    document.activity("trial{}Execution".format(trial.id), trial.start, trial.finish,
                      [("nowCommand", trial.command),
                       ("parentId", trial.parent_id),
                       ("inheritedId", trial.inherited_id)])

    document.wasAssociatedWith("trial{}Execution".format(trial.id), trial.script, None,
                               "trial{}ExecutionByScript".format(trial.id))
