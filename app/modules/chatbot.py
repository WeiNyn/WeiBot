import os
import sys
from typing import Dict, Tuple, Any
import socketio

from pydantic.main import BaseModel

sys.path.append(os.getcwd())

from controller.server_controller import Controller, UserConversations
from channels.botframework import BotFramework


class Message(BaseModel):
    """
    Input scheme for sending messages through rest api
    """
    message: str
    user_id: str


async def send_rest_func(message: Message, user_conversations: UserConversations, controller: Controller) -> Tuple[Dict[str, Any], UserConversations, Controller]:
    """
    Receive message and give response

    :param message: Message class - user input request as Message type
    :param user_conversations: UserConversations - user_conversation manager
    :param controller: Controller - main controller for server
    :return: tuple(output, user_conversation, controller)
    """

    user_id = message.user_id
    user_input = message.message

    # Query user stats from database
    user_state = user_conversations(user_id)

    # Handle current conversation
    output = controller(user_state, user_input).__dict__

    user_conversations.save_to_db(user_id=user_id)

    return output, user_conversations, controller


async def send_bot_framework_func(user_input: Dict[str, Any], user_conversations: UserConversations, controller: Controller, bot_framework: BotFramework, sio: socketio.Client) -> Tuple[UserConversations, Controller, BotFramework]:
    """
    Receive message from Skype and send back to user on Skype

    :param user_input: Standard format from Skype
    :param user_conversations: UserConversations - user_conversations manager
    :param controller: Controller - main controller for server
    :param bot_framework: BotFramework - bot_framework channel
    :param sio - socketio.Client - the socketio for ARM system
    :return: tuple(user_conversations, controller, botframework)
    """
    user_input = bot_framework.translate_botframework_input(user_input)

    user_id = user_input["id"]
    user_message = user_input["text"]
    user_name = user_input["user_name"]

    # If Arm is on, this path check the 'u2u' status of user and send message to ARM system instead of Skype
    if sio is not None:
        u2u_result = await handle_u2u_message(user_input=user_input, user_conversations=user_conversations, sio=sio)
        if u2u_result is True:
            return user_conversations, controller, bot_framework

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

    return user_conversations, controller, bot_framework


async def handle_u2u_message(user_input: Dict[str, Any], user_conversations: UserConversations, sio: socketio.Client) -> bool:
    """
    If ARM system is on, this function check the 'u2u' status of user and send to ARM instead of Skype

    :param user_input: Standard format from Skype
    :param user_conversations: UserConversations - user_conversations manager
    :param sio: socketio.Client - the socketio for the ARM system
    :return: bool - Redirect to ARM or not
    """
    user_id = user_input["id"]
    user_message = user_input["text"]

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
            print(f"Cannot send event to socket with error {ex}")
            return False

    return False
