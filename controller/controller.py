import os
import sys

sys.path.append(os.getcwd())

from typing import Dict, List, Any
import inquirer

from parsers.flow_map import FlowMap
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper


class UserChatState:
    """
    object that store flow_map, nlu pipelines and current state of conversation
    """
    def __init__(self, nlu: Wrapper,
                 flow_map: FlowMap,
                 user_id: str, version: str,
                 intent: Dict[str, Any] = None,
                 entities: List[Dict[str, Any]] = None,
                 slots: Dict[str, Any] = None):
        """
        Create user_chat_state
        :param nlu: DIETClassifierWrapper object
        :param flow_map: FlowMap object
        :param user_id: unique identifier of user
        :param version: version of system
        :param intent: dict(name, intent_ranking, priority) - latest intent of user
        :param entities: list(dict(entity_name, text, ...) - latest entities of user message
        :param slots: dict(slots_name) - dictionary of current conversation's slots
        """
        self.nlu = nlu
        self.flow_map = flow_map

        self.user_id = user_id
        self.version = version

        self.intent = dict(name=None, intent_ranking={}) if not intent else intent
        self.entities = [] if not entities else entities
        self.slots = dict() if not slots else slots

        self._check()

        self.loop_stack = 0

    def _check(self):
        """
        Validate given parameters and create needed attributes
        :return: None
        """
        if self.intent["name"] is not None:
            if self.intent["name"] not in self.flow_map.intents_list:
                raise ValueError(f"Intent {self.intent['name']} is not an available intent")

            for key in self.intent["intent_ranking"].keys():
                if key not in self.flow_map.intents_list:
                    raise ValueError(f"Intent {key} is not an available intent")

        for entity in self.entities:
            if entity["entity_name"] not in self.flow_map.entities_list:
                raise ValueError(f"Entity {entity['entity_name']} is not an available entity")

            if entity.get("text", None) is None:
                raise ValueError(f"Entity object should have 'text' attribute")

        for slot in self.slots.keys():
            if slot not in self.flow_map.slots_list:
                raise ValueError(f"Slot {slot} is not an available slot")

    def translate_user_input(self, user_input: str):
        """
        Predict user intent and entities, set them to the main object
        :param user_input: str - user message
        :return: None
        """
        sentences = [user_input]
        predicted_output = self.nlu.predict(sentences)[0]

        intent = dict(name=predicted_output["intent"],
                      intent_ranking=predicted_output["intent_ranking"])

        if intent.get("name", None) not in self.flow_map.actions_map.keys():
            intent["name"] = "default"
            intent["priority"] = 0

        else:
            intent["priority"] = self.flow_map.actions_map[intent.get("name")].priority

        entities = predicted_output["entities"]

        self.intent = intent
        self.entities = entities

    def handle_flow(self, trigger_intent: str = None, request_slot: str = None):
        """
        Handle the conversation based on give event, if not trigger_intent or request_slot event raised, pass nothing to the function
        :param trigger_intent: str - the name of triggered intent
        :param request_slot: str - the name of requested slot
        :return: EventOutput - the next event
        """
        if trigger_intent:
            self.intent = dict(name=trigger_intent, intent_ranking=dict())
            events = self.flow_map.actions_map[self.intent["name"]](self.intent, self.entities, self.slots)
            return events

        elif request_slot:
            events = self.flow_map.requests_map[request_slot](self.intent, self.entities, self.slots)
            return events

        else:
            events = self.flow_map.actions_map[self.intent["name"]](self.intent, self.entities, self.slots)
            return events

    def __call__(self):
        """
        Start the conversation
        :return: None
        """

        print("Enter something plz")
        user_input = input()
        self.translate_user_input(user_input)

        events = self.handle_flow().__dict__
        while True:
            if self.loop_stack > 10:
                break

            if events.get("set_slot", None) is not None:
                self.slots.update(events.get("set_slot"))

            if events.get("text", None) is not None:
                self.loop_stack = 0
                text = [inquirer.Text("text", message=(events.get("text") + " - "))]

                user_input = inquirer.prompt(text).get("text")

                self.translate_user_input(user_input)

            elif events.get("button", None) is not None:
                self.loop_stack = 0
                button = [inquirer.List("button", message=events.get("button").get("text"), choices=[button["text"] for button in events.get("button").get("button")])]

                user_input = inquirer.prompt(button).get("button")

                self.translate_user_input(user_input)

            if events.get("trigger_intent", None) is not None:
                self.loop_stack += 1
                trigger_intent = events.get("trigger_intent")
                events = self.handle_flow(trigger_intent=trigger_intent).__dict__
                continue

            if events.get("request_slot", None) is not None or self.slots.get("request_slot", None) is not None:
                request_slot = events.get("request_slot", None)
                if not events.get("request_slot", None):
                    request_slot = self.slots.get("request_slot")

                self.loop_stack += 1
                events = self.handle_flow(request_slot=request_slot).__dict__
                continue

            events = self.handle_flow().__dict__
