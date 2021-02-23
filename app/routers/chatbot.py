import os
import sys

from fastapi import Body, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic.main import BaseModel

sys.path.append(os.getcwd())

from controller.server_controller import Controller, UserConversations
from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper
from channels.botframework import BotFramework
from actions.defined_actions import *

from app.setting.setting import Setting

router = APIRouter()

nlu: Wrapper = Wrapper(Setting.model_config)
flow_map: FlowMap = FlowMap(Setting.flow_config, Setting.domain_config)
controller: Controller = Controller(nlu=nlu, flow_map=flow_map, version=Setting.version,
                                    base_action_class=Setting.base_action_class)

user_conversations: UserConversations = UserConversations(db=Setting.user_db,
                                                          entities_list=flow_map.entities_list,
                                                          intents_list=flow_map.intents_list,
                                                          slots_list=flow_map.slots_list,
                                                          user_limit=10)

bot_framework = BotFramework(Setting.app_id, Setting.app_password, Setting.bot)

# ARM required socketio setup
if Setting.arm_on:
    import socketio

    sio = socketio.Client()
    sio.connect(Setting.arm_socket)


class Message(BaseModel):
    """
    Input scheme for /chatbot/rest
    """
    message: str
    user_id: str


@router.post("/rest/")
async def send_rest(message: Message):
    """
    Receive message and give response
    :param message: Message object type
    :return: None
    """
    user_id = message.user_id
    user_input = message.message

    global user_conversations
    global controller

    # Query user stats from database
    user_state = user_conversations(user_id)

    # Handle current conversation
    output = controller(user_state, user_input).__dict__

    user_conversations.save_to_db(user_id=user_id)

    responses = jsonable_encoder(output)
    return JSONResponse(responses)


@router.post("/botframework/")
async def send_botframework(user_input: Dict[str, Any] = Body(...)):
    """
    Receive message from Skype and send back to user on Skype
    :param user_input: Standard format from Skype
    :return: None
    """
    user_input = bot_framework.translate_botframework_input(user_input)

    user_id = user_input["id"]
    user_message = user_input["text"]
    user_name = user_input["user_name"]

    global user_conversations
    global controller

    # If Arm is on, this path check the 'u2u' status of user and send message to ARM system instead of Skype
    if Setting.arm_on:
        u2u_result = await handle_u2u_message(user_input=user_input)
        if u2u_result is True:
            return None

    # Query user stats from database
    user_state = user_conversations(user_id, user_name)

    # Handle current conversation
    output = controller(user_state, user_message).__dict__

    user_conversations.save_to_db(user_id=user_id)

    text = output.get("text", None)
    button = output.get("button", None)

    bot_framework.prepare_message(recipient_id=user_input["recipient_id"], user_name=user_input["user_name"],
                                  message_data={"text": text})

    if button is not None:
        await bot_framework.send_text_with_buttons(recipient_id=user_input["recipient_id"],
                                                   user_name=user_input["user_name"],
                                                   conversation=user_input["conversation"], text=text, buttons=button)

    else:
        await bot_framework.send_text_message(recipient_id=user_input["recipient_id"],
                                              user_name=user_input["user_name"],
                                              conversation=user_input["conversation"], text=text)


async def handle_u2u_message(user_input: Dict[str, Any]):
    """
    If ARM system is on, this function check the 'u2u' status of user and send to ARM instead of Skype
    :param user_input: Standard format from Skype
    :return: bool - Redirect to ARM or not
    """
    user_id = user_input["id"]
    user_message = user_input["text"]

    global user_conversations

    arm_status = user_conversations.db.get_user_status(user_id=user_id)

    if arm_status:
        u2u = arm_status["u2u"]
        floor = arm_status["floor"]

        if not u2u:
            return False

        if user_message == "(open_door)":
            event_name = "open_door"
        elif user_message == "(close_door)":
            event_name = "close_door"
        else:
            event_name = "chatbotRely"

        try:
            sio.emit(event_name, {"floor": floor, "msg": user_message})
            return True

        except Exception as ex:
            return False

    return False

