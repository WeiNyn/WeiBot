import os
import sys

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic.main import BaseModel

sys.path.append(os.getcwd())

from controller.server_controller import Controller, UserConversations
from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper
from actions.defined_actions import *

MODEL_CONFIG = "/home/weinyn/Documents/WeiBot/config/config.yml"
FLOW_CONFIG = "/home/weinyn/Documents/WeiBot/config/final_config.yml"
DOMAIN_CONFIG = "/home/weinyn/Documents/WeiBot/config/domain.yml"

nlu = Wrapper(MODEL_CONFIG)
flow_map = FlowMap(FLOW_CONFIG, DOMAIN_CONFIG)
controller: Controller = Controller(nlu=nlu, flow_map=flow_map, version="v0.0", base_action_class=BaseActionClass)

user_conversations: UserConversations = UserConversations(db="database/test_db.db",
                                                          entities_list=flow_map.entities_list,
                                                          intents_list=flow_map.intents_list,
                                                          slots_list=flow_map.slots_list,
                                                          user_limit=10)

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

    print(user_state.button)
    print(user_state.synonym_dict)

    output = controller(user_state, user_input).__dict__

    user_conversations.save_to_db(user_id=user_id)

    responses = jsonable_encoder(output)

    print(user_state.response.__dict__)

    return JSONResponse(responses)
