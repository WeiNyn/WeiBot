import os
import sys
import io
import base64
from datetime import datetime
from PIL import Image
from typing import Tuple, Dict, Any, Optional

from pydantic.main import BaseModel

sys.path.append(os.getcwd())

from database.database import ChatStateDB
from channels.botframework import BotFramework
from app.setting.setting import Setting


HOST_LINK = Setting.host_link
IMAGES_PATH = Setting.images_path


class SendData(BaseModel):
    """
    Input scheme for ARM system
    """
    message: str
    id: str
    floor: str
    img: str
    type: int


async def send_message_func(request: SendData, bot_framework: BotFramework, db: ChatStateDB) -> Tuple[Optional[Dict[str, Any]], BotFramework]:
    """
    Handle request from ARM and send message to Skype user
     - message: str - text message to user
     - id: str - id of Skype user
     - img: str - base64 image as string format
     - type: int
            + 1 - send message to user, if user's u2u is on, return failed message
            + 2 - force turn of u2u status of user and send message to that user
            + 3 - send message to user regard of its u2u status
     - floor: floor of ARM device

    :param request: dict(message, id, img, type, floor) - explained in the doc
    :param bot_framework: BotFramework - bot_framework channel
    :param db: ChatStateDB - user status database
    :return: bot_framework
    """
    message = request.message
    id = request.id
    img = request.img
    type = request.type
    floor = request.floor

    if not 0 < type < 4:
        return {"status": False}, bot_framework

    # Get the requested user status
    arm_status = db.get_user_status(user_id=id)
    if not arm_status:
        return {"status": False}, bot_framework

    # Get all user status
    arm_statuses = db.fetch_arm_status()

    # This block reset u2u for all user that offline from ARM for 3 minute
    for user in arm_statuses:
        if datetime.today().timestamp() - float(user["timestamp"]) > 60.0*3:
            user["u2u"] = False
            if user["user_id"] == id:
                arm_status["u2u"] = False

    if type == 1:
        if arm_status["u2u"]:
            return {"status": False}, bot_framework
        else:
            arm_status["u2u"] = True
            arm_status["timestamp"] = datetime.today().timestamp()

    elif type == 2:
        arm_status["u2u"] = False

    elif type == 3:
        for user in arm_statuses:
            if user["user_id"] == id:
                user["u2u"] = True
                user["floor"] = floor
                user["timestamp"] = datetime.today().timestamp()

                arm_status["u2u"] = True
                arm_status["floor"] = floor
                arm_status["timestamp"] = datetime.today().timestamp()

            else:
                if user["floor"] == floor:
                    user["u2u"] = False

    if not len(message):
        return {"status": True}, bot_framework

    img_url = None
    if img:
        try:
            await create_image(img, arm_status["floor"])
        except Exception as ex:
            print(f"Cannot convert string image {ex}")

        img_url = f"{HOST_LINK}/ARM/img?floor={str(arm_status['floor'])}.png&timestamp={str(datetime.today().timestamp())}"

    bot_framework.prepare_message(recipient_id=id, user_name=arm_status["user_name"], message_data={"text": message})

    if img:
        await bot_framework.send_image_url(recipient_id=id, user_name=arm_status["user_name"], conversation={"id": id}, image=img_url)

    await bot_framework.send_text_message(recipient_id=id, user_name=arm_status["user_name"], conversation={"id": id}, text=message)

    for user in arm_statuses:
        if user["user_id"] == id:
            user_id = arm_status["user_id"]
            user_name = arm_status["user_name"]
            u2u = arm_status["u2u"]
            floor = arm_status["floor"]

        else:
            user_id = user["user_id"]
            user_name = user["user_name"]
            u2u = user["u2u"]
            floor = user["floor"]

        db.change_user_status(user_id=user_id, user_name=user_name, u2u=u2u, floor=floor)

    return None, bot_framework


async def create_image(img: str, floor: str):
    """
    Create image and save to IMAGES_PATH by the base64 image

    :param img: str - base64 image
    :param floor: str - name of the ARM floor (used for setting name of image)
    :return: None
    """
    if "data:image" in img:
        string_split = img.split(",")
        if len(string_split) > 1:
            img = string_split[1]

    pil_img = Image.open(io.BytesIO(base64.b64decode(img)))
    pil_img.save(f"{IMAGES_PATH}/{floor}.png")
    del pil_img


async def get_user_func(db: ChatStateDB) -> Dict[str, Any]:
    """
    Get all user status

    :return: dict(user_id) - dictionary of user status, map by user_id
    """
    arm_status = db.fetch_arm_status()

    result_dict = dict()

    for user in arm_status:
        result_dict[user["user_id"]] = dict(
            u2u=user["u2u"],
            user_name=user["user_name"],
            timestamp=user["timestamp"],
            floor=user["floor"]
        )

    return result_dict
