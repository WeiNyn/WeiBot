import logging
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

logging.basicConfig(level=logging.ERROR)

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse
from pydantic.main import BaseModel

app = FastAPI(host="0.0.0.0")

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

sys.path.append(os.getcwd())

from app.modules.chatbot import Message, send_rest_func, send_bot_framework_func
from app.modules.ARM import SendData, send_message_func, get_user_func
from app.modules.CMS import HIGH_LEVEL_CONFIG, NLU_CONFIG, DATASET, change_dataset, add_qna, remove_qna, save_qna
from app.modules.DB import get_conversation, get_messages

from controller.server_controller import Controller, UserConversations
from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper
from channels.botframework import BotFramework
from actions.defined_actions import *

from app.setting.setting import Setting

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
else:
    sio = None


@app.post("/webhooks/rest/webhook")
async def send_rest(message: Message):
    global user_conversations
    global controller

    try:
        output, user_conversations, controller = await send_rest_func(message=message,
                                                                      user_conversations=user_conversations,
                                                                      controller=controller)

    except Exception as ex:
        logging.error(f"Error: Chatbot's rest channel error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder(output), status_code=200)


@app.post("/chatbot/botframework/")
async def send_bot_framework(user_input: Dict[str, Any] = Body(...)):
    global user_conversations
    global controller
    global bot_framework

    try:
        user_conversations, controller, bot_framework = await send_bot_framework_func(user_input=user_input,
                                                                                      user_conversations=user_conversations,
                                                                                      controller=controller,
                                                                                      bot_framework=bot_framework,
                                                                                      sio=sio)

    except Exception as ex:
        logging.error(f"Error: Chatbot's botframework channel error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


@app.post("/ARM/send/")
async def send_arm(request: SendData):
    global bot_framework
    global user_conversations

    try:
        output, bot_framework = await send_message_func(request=request, bot_framework=bot_framework,
                                                        db=user_conversations.db)

    except Exception as ex:
        logging.error(f"Error: ARM send message failed {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    if output is not None and output.get("status", None) is False:
        return JSONResponse(jsonable_encoder(output), status_code=200)

    return JSONResponse(jsonable_encoder({"status": True}), status_code=200)


@app.get("/ARM/users")
async def get_user():
    global user_conversations

    try:
        result = await get_user_func(user_conversations.db)

    except Exception as ex:
        logging.error(f"Error: ARM get users error {ex}")
        return JSONResponse(jsonable_encoder({"error": ex}), status_code=500)

    return JSONResponse(jsonable_encoder(result), status_code=200)


@app.get("/ARM/img/")
async def get_img(floor: str, timestamp: str):
    """
    Get image from IMAGES_PATH folder

    :param floor: str - should be {floor}.png
    :param timestamp: str - timestamp to make the link difference every time it called
    :return: Image file
    """
    return FileResponse(f"{Setting.images_path}/{floor}")


@app.get("/CMS/qna")
async def get_qna():
    return JSONResponse(jsonable_encoder(HIGH_LEVEL_CONFIG))


@app.get("/CMS/nlu_config")
async def get_nlu_config():
    return JSONResponse(jsonable_encoder(NLU_CONFIG))


@app.get("/CMS/dataset")
async def get_dataset():
    return JSONResponse(jsonable_encoder(DATASET))


@app.post("/CMS/dataset")
async def fetch_dataset(intent_name: str):
    if not DATASET.get(intent_name, None):
        return JSONResponse(jsonable_encoder({"error": f"{intent_name} not found"}), status_code=400)

    return JSONResponse(jsonable_encoder(DATASET[intent_name]))


class Entity(BaseModel):
    entity: str
    entity_name: str
    position: Tuple[int, int]
    synonym: Optional[str]


class Example(BaseModel):
    text: str
    entities: List[Entity]


class QNA(BaseModel):
    intent: str
    working_type: Optional[Dict[str, Any]]
    text: Optional[str]
    examples: List[Example]


@app.post("/CMS/change_qna/")
async def change_qna(qna: QNA):
    intent_name = qna.intent
    working_type = qna.working_type
    text = qna.text
    examples = qna.examples

    examples = [dict(
        text=ex.text,
        entities=[entity.__dict__ for entity in ex.entities]
    )
        for ex in examples]

    if working_type is None and text is None:
        return JSONResponse(jsonable_encoder({"error": "at least working_type or text must be specified"}),
                            status_code=400)

    if working_type is not None and text is not None:
        return JSONResponse(jsonable_encoder({"error": "only give working_type or text"}), status_code=400)

    intent_data = dict(
        intent=intent_name
    )

    if working_type is not None:
        intent_data["working_type"] = working_type

    else:
        intent_data["text"] = text

    try:
        await add_qna(intent=intent_data, examples=examples)

    except Exception as ex:
        logging.error(f"Error: Change qna error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


@app.post("/CMS/remove_qna")
async def rm_qna(intent_name: str):
    try:
        await remove_qna(intent_name=intent_name)

    except Exception as ex:
        logging.error(f"Error: Remove QnA error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


@app.post("/CMS/save_qna")
async def save(dataset_folder: str):
    try:
        await save_qna(dataset_folder=dataset_folder)

    except Exception as ex:
        logging.error(f"Error: Save QnA error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


class DatasetExamples(BaseModel):
    intent: str
    examples: List[Example]


@app.post("/CMS/change_dataset/")
async def change_dataset(dataset: DatasetExamples):
    intent = dataset.intent
    examples = dataset.examples

    examples = [dict(
        text=ex.text,
        entities=[entity.__dict__ for entity in ex.entities]
    )
        for ex in examples]

    try:
        await change_dataset(intent_name=intent, examples=examples)

    except Exception as ex:
        logging.error(f"Error: chagne dataset error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


@app.post("/DB/user_conversation")
async def get_user(user_id: str):
    try:
        global user_conversations
        return JSONResponse(jsonable_encoder(await get_conversation(user_conversations.db, user_id=user_id)),
                            status_code=200)

    except Exception as ex:
        logging.error(f"get user conversation error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)


@app.get("/DB/messages")
async def fetch_user_messages():
    try:
        global user_conversations
        return JSONResponse(jsonable_encoder(await get_messages(user_conversations.db)), status_code=200)

    except Exception as ex:
        logging.error(f"get user conversation error {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)


@app.get("/Model/train")
async def train_model(save_folder: str = None):
    if not save_folder:
        save_folder = f"models/model_{datetime.today().timestamp()}"

    else:
        save_folder = f"models/{save_folder}"

    try:
        nlu.train_model(save_folder=save_folder)

    except Exception as ex:
        logging.error(f"ERROR: Cannot train model {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)


@app.get("Model/reload")
async def reload():
    global nlu
    global flow_map
    global user_conversations
    global controller

    try:
        new_nlu: Wrapper = Wrapper(Setting.model_config)
        new_flow_map: FlowMap = FlowMap(Setting.flow_config, Setting.domain_config)
        new_controller: Controller = Controller(nlu=new_nlu, flow_map=new_flow_map, version=Setting.version,
                                                base_action_class=Setting.base_action_class)
        new_user_conversations: UserConversations = UserConversations(db=Setting.user_db,
                                                                      entities_list=new_flow_map.entities_list,
                                                                      intents_list=new_flow_map.intents_list,
                                                                      slots_list=new_flow_map.slots_list, user_limit=10)

    except Exception as ex:
        logging.error(f"ERROR: Cannot reload chatbot {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    try:
        nlu = None
        flow_map = None
        user_conversations = None
        controller = None

        nlu = new_nlu
        flow_map = new_flow_map
        user_conversations = new_user_conversations
        controller = new_controller

    except Exception as ex:
        logging.error(f"ERROR: Cannot reload chatbot {ex}")
        return JSONResponse(jsonable_encoder({"error": str(ex)}), status_code=500)

    return JSONResponse(jsonable_encoder({"status": "success"}), status_code=200)
