import json
from datetime import datetime, timedelta
import requests

from typing import Dict, List, Any, Optional

MICROSOFT_OAUTH2_URL = "https://login.microsoftonline.com"

MICROSOFT_OAUTH2_PATH = "botframework.com/oauth2/v2.0/token"


class BotFramework:
    """BotFramework that handle input and output from Azure service"""
    def __init__(self, app_id: str, app_password: str, bot: Dict[str, Any]):
        """
        Create botframework

        :param app_id: str - app id
        :param app_password: str - app password
        :param bot: dict() - bot information
        """
        self.token_expiration_date = datetime.now()
        self.headers = None
        self.service_url = "https://smba.trafficmanager.net/apis/"
        self.oauth2_url = "https://login.microsoftonline.com"
        self.oauth2_path = "botframework.com/oauth2/v2.0/token"
        self.app_id = app_id
        self.app_password = app_password
        self.global_uri = f"{self.service_url}v3/"
        self.bot = bot

    async def _get_headers(self) -> Optional[Dict[str, Any]]:
        """
        Get the authorization headers if not available

        :return: dict() - the headers
        """
        if self.token_expiration_date < datetime.now():
            uri = f"{self.oauth2_url}/{self.oauth2_path}"
            grant_type = "client_credentials"
            scope = "https://api.botframework.com/.default"
            payload = {
                "client_id": self.app_id,
                "client_secret": self.app_password,
                "grant_type": grant_type,
                "scope": scope,
            }

            token_response = requests.post(uri, data=payload)

            if token_response.ok:
                token_data = token_response.json()
                access_token = token_data["access_token"]
                token_expiration = token_data["expires_in"]

                delta = timedelta(seconds=int(token_expiration))
                self.token_expiration_date = datetime.now() + delta

                self.headers = {
                    "content-type": "application/json",
                    "Authorization": "Bearer %s" % access_token,
                }

                return self.headers
            else:
                raise RuntimeError(f"Cannot get BotFramework token")

        else:
            return self.headers

    def prepare_message(self, recipient_id: str, user_name: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data to send message

        :param recipient_id: str - id of recipient conversation
        :param user_name: str - name of user
        :param message_data: dict() - data of message
        :return: dict() - data of message
        """
        data = {
            "type": "message",
            "recipient": {"id": recipient_id},
            "from": self.bot,
            "channelData": {"notification": {"alert": "true"}},
            "text": "",
        }

        data.update(message_data)

        data["text"] = data["text"].replace("__user__", user_name)

        return data

    async def send(self, message_data: Dict[str, Any], conversation) -> None:
        """
        send message to Azure

        :param message_data: dict() - message data
        :param conversation: dict() - the conversation to send
        :return: None
        """
        post_message_uri = "{}conversations/{}/activities".format(
            self.global_uri, conversation["id"]
        )
        headers = await self._get_headers()

        send_response = requests.post(
            post_message_uri, headers=headers, data=json.dumps(message_data)
        )

        if not send_response.ok:
            raise RuntimeError(f"Error truing to send BotFramework message. response {send_response.text}")

    async def send_text_message(self, recipient_id: str, user_name: str, conversation: Dict[str, Any], text: str) -> None:
        """
        Send normal text message

        :param recipient_id: str - recipient id
        :param user_name: str - user name
        :param conversation: dict(id) - conversation from skype request
        :param text: str - text message
        :return: None
        """
        for message_part in text.strip().split("\n\n"):
            text_message = {"text": message_part}
            message = self.prepare_message(conversation["id"], user_name, text_message)
            await self.send(message, conversation)

    async def send_image_url(self, recipient_id: str, user_name: str, conversation: Dict[str, Any], image: str) -> None:
        """
        Send image with URL

        :param recipient_id: str - recipient id
        :param user_name: str - user name
        :param conversation: dict(id) - conversation from skype request
        :param image: str - url of image
        :return: None
        """
        hero_content = {
            "contentType": "application/vnd.microsoft.card.hero",
            "content": {"images": [{"url": image}]},
        }

        image_message = {"attachments": [hero_content]}
        message = self.prepare_message(conversation["id"], user_name, image_message)
        await self.send(message, conversation)

    async def send_text_with_buttons(self, recipient_id: str, user_name: str, conversation: Dict[str, Any], text: str, buttons: List[str]) -> None:
        """
        Send text message with selection buttons

        :param recipient_id: str - recipient id
        :param user_name: str - user name
        :param conversation: dict(id) - conversation from skype request
        :param text: str - text message
        :param buttons: list(str) - list of selection
        :return: None
        """
        buttons = [{
            "type": "imBack",
            "value": button,
            "title": button
            }
            for button in buttons
        ]

        hero_content = {
            "contentType": "application/vnd.microsoft.card.hero",
            "content": {"title": text, "buttons": buttons},
        }

        buttons_message = {"attachments": [hero_content]}
        message = self.prepare_message(conversation["id"], user_name, buttons_message)
        await self.send(message, conversation)

    @staticmethod
    def translate_botframework_input(user_input: Dict[str, Any]):
        """
        Translate the request from skype to minimize form

        :param user_input: dict() - request from skupe
        :return: dict() - data to process
        """
        text = user_input["text"]
        id = user_input["from"]["id"]
        user_name = user_input["from"]["name"]
        conversation = user_input["conversation"]
        recipient_id = user_input["recipient"]["id"]

        return dict(
            text=text,
            id=id,
            user_name=user_name,
            conversation=conversation,
            recipient_id=recipient_id
        )

