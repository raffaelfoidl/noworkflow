import prov.model as provo
import prov.dot as provo_dot

from noworkflow.now.persistence.models import Trial
from noworkflow.now.persistence.models.diff import Diff as DiffModel
from noworkflow.now.utils.io import print_msg


def export_diff(diff: DiffModel, args):
    document = provo.ProvDocument()
    document.set_default_namespace(args.defaultns)

    print_msg("Exporting comparison provenance of trials {} and {} in PROV-O format"
              .format(diff.trial1.id, diff.trial2.id), force=True)

    basic_info(diff, document)

    with open("hello.pn", "w") as file:
        document.serialize(destination=file, format="provn")
    provo_dot.prov_to_dot(document).write("hello.pdf", format="pdf")


def basic_info(diff: DiffModel, document: provo.ProvDocument):
    trial_info(diff.trial1, document)
    trial_info(diff.trial2, document)

    influencee_id = max(diff.trial1.id, diff.trial2.id)
    influencer_id = min(diff.trial1.id, diff.trial2.id)
    document.wasInfluencedBy("trial{}Execution".format(influencee_id),
                             "trial{}Execution".format(influencer_id),
                             "trial{}After{}".format(influencee_id, influencer_id),
                             [(provo.PROV_TYPE, "successor")])


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
