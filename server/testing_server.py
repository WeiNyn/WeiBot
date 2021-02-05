import os
import sys

from fastapi import FastAPI, Body
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic.main import BaseModel

sys.path.append(os.getcwd())

from controller.server_controller import Controller, UserConversations
from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper
from channels.botframework import BotFramework
from actions.defined_actions import *

MODEL_CONFIG = "/home/weinyn/Documents/WeiBot/config/config.yml"
FLOW_CONFIG = "/home/weinyn/Documents/WeiBot/config/final_config.yml"
DOMAIN_CONFIG = "/home/weinyn/Documents/WeiBot/config/domain.yml"

APP_ID = "c072edf3-5800-4c7b-939a-107508981bf0"
APP_PASSWORD = "~gKRJs8q..l32CgS-4WD84Zej-Dl8.p5bo"
BOT = {
    "id": "28:c072edf3-5800-4c7b-939a-107508981bf0",
    "name": "CLeVer"
}

nlu = Wrapper(MODEL_CONFIG)
flow_map = FlowMap(FLOW_CONFIG, DOMAIN_CONFIG)
controller: Controller = Controller(nlu=nlu, flow_map=flow_map, version="v0.0", base_action_class=BaseActionClass)

user_conversations: UserConversations = UserConversations(db="database/test_db.db",
                                                          entities_list=flow_map.entities_list,
                                                          intents_list=flow_map.intents_list,
                                                          slots_list=flow_map.slots_list,
                                                          user_limit=10)

bot_framework = BotFramework(APP_ID, APP_PASSWORD, BOT)

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    message: str
    user_id: str


@app.post("/send/")
async def send(message: Message):
    user_id = message.user_id
    user_input = message.message

    global user_conversations
    global controller

    user_state = user_conversations(user_id)

    output = controller(user_state, user_input).__dict__

    user_conversations.save_to_db(user_id=user_id)

    responses = jsonable_encoder(output)

    return JSONResponse(responses)


@app.post("/test/")
async def test(user_input: Dict[str, Any] = Body(...)):
    user_input = bot_framework.translate_botframework_input(user_input)

    user_id = user_input["id"]
    user_message = user_input["text"]

    global user_conversations
    global controller

    user_state = user_conversations(user_id)

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
