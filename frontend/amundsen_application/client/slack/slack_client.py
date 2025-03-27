# https://slack.dev/python-slack-sdk/web/index.html#messaging
# https://pandeynandancse.medium.com/slack-send-attachments-using-python-webclient-baa39974ceea
from pathlib import Path
import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


LOGGER = logging.getLogger(__name__)


class SlackClient():
    def __init__(self,
                 token: str) -> None:

        self.client = WebClient(token=token)


    def post(self,
             channel: str,
             message: str):
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
        except SlackApiError as e:
            LOGGER.exception(e)
            raise e

    def upload(self,
               channel: str, # Must use the channel ID not the name
               file_path: str,
               title: str = None,
               comment: str = None):
        try:
            response = self.client.files_upload_v2(
                channel=channel,
                file=file_path,
                title=title,
                initial_comment=comment
            )
        except SlackApiError as e:
            LOGGER.exception(e)
            raise e
