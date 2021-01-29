import os
import sys

sys.path.append(os.getcwd())

from controller.controller import UserChatState
from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper

MODEL_CONFIG = "/home/weinyn/Documents/ChatbotController/config/config.yml"
FLOW_CONFIG = "/home/weinyn/Documents/ChatbotController/config/flow_config.yml"
DOMAIN_CONFIG = "/home/weinyn/Documents/ChatbotController/config/domain.yml"

nlu = Wrapper(MODEL_CONFIG)
flow_map = FlowMap(FLOW_CONFIG, DOMAIN_CONFIG)

controller = UserChatState(flow_map=flow_map, nlu=nlu, user_id="admin", version="v0.0")

if __name__ == "__main__":
    controller()
