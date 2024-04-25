from bcr_api.bwproject import BWProject
from bcr_api.bwresources import BWSentiment
import logging

logger = logging.getLogger("bcr_api")

USER_NAME = "mstroik@quadstrat.com"
PROJECT_NAME = "Quadrant"
API_TOKEN = "1536f504-8ec2-4bbf-bee6-4ee58e3c5308"
PROJECT_ID = "1998281989"

class CallbackHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)

def update_bw_sentiment(updated_sentiment_dict, log_callback):
    handler = CallbackHandler(log_callback)
    logger.addHandler(handler)

    project = BWProject(username=USER_NAME, token=API_TOKEN, project_name=PROJECT_NAME, project_id=PROJECT_ID)
    mentions = BWSentiment(project)
    mentions.patch_mentions(updated_sentiment_dict)

    logger.removeHandler(handler)
