from typing import Optional
import warnings

from actions.defined_actions import *
from database.database import ChatStateDB
from nlu_pipelines.DIETClassifier.src.models.wrapper import DIETClassifierWrapper as Wrapper
from parsers.event import ButtonEvent, EventOutput, ButtonTrigger
from parsers.flow_map import FlowMap


class ConversationState:
    def __init__(self,
                 user_id: str,
                 version: str,
                 entities_list: List[str],
                 intents_list: List[str],
                 slots_list: List[str],
                 intent: Dict[str, Any] = None,
                 entities: List[Dict[str, Any]] = None,
                 slots: Dict[str, Any] = None,
                 button: Dict[str, Any] = None,
                 events: Dict[str, Any] = None,
                 loop_stack: int = 0,
                 response: Dict[str, Any] = None):
        self.user_id: str = user_id
        self.version: str = version

        self.intent: Dict[str, Any] = dict(name="default", intent_ranking={}, priority=0) if not intent else intent
        self.entities: List[Dict[str, Any]] = [] if not entities else entities
        self.slots: Dict[str, Any] = dict() if not slots else slots

        self.button_dict: Dict[str, Any] = button
        self.button: Optional[Dict[str, ButtonTrigger]] = None

        self.events: EventOutput = EventOutput(dict()) if not events else EventOutput(events)

        self.loop_stack: int = loop_stack

        self.response_dict: Dict[str, Any] = response
        self.response: Optional[MessageOutput] = None

        self._check(entities_list, intents_list, slots_list)

    def _check(self, entities_list: List[str], intents_list: List[str], slots_list: List[str]):
        if self.intent["name"] not in intents_list:
            raise ValueError(f"Intent {self.intent['name']} is not an available intent")

        for entity in self.entities:
            if entity["entity_name"] not in entities_list:
                raise ValueError(f"Entity {entity['entity_name']} is not an available entity")

        for keys in self.slots.keys():
            if keys not in slots_list:
                raise ValueError(f"Slot {keys} is not an available slot")

        for key in self.events.__dict__.keys():
            if key not in ["text", "action", "button", "set_slot", "trigger_intent", "request_slot"]:
                raise ValueError(f"Event {key} is not an available event")

        if self.button_dict is not None:
            self.button = dict()
            for key, value in self.button_dict:
                self.button[key] = ButtonTrigger(value, entities_list, intents_list, slots_list)

        else:
            self.button = None

        if self.response_dict:
            if self.response_dict.get("text", None) is None and self.response_dict.get("button", None) is None:
                raise ValueError(f"response_dict must have text or button")

            if not isinstance(self.response_dict.get('text', None), str):
                raise ValueError(f"'text' must be a string, not {self.response_dict.get('text')}")

            if not isinstance(self.response_dict.get('button', None), list):
                raise ValueError(f"'button' must be a list of string, not {self.response_dict.get('button')}")

            self.response = MessageOutput(text=self.response_dict.get('text'), button=self.response_dict.get("button"))

        else:
            self.response = None

    def export(self) -> Dict[str, Any]:
        return dict(
            user_id=self.user_id,
            version=self.version,
            intent=self.intent,
            slots=self.slots,
            entities=self.entities,
            events=self.events.__dict__,
            button=None if self.button is None else {k: v.export() for k, v in self.button.items()},
            loop_stack=self.loop_stack,
            response=None if self.response is None else self.response.__dict__
        )


class MessageOutput:
    def __init__(self, text: str = None, button: List[str] = None):
        self.text = text
        self.button = button


class Controller:
    def __init__(self, nlu: Wrapper,
                 flow_map: FlowMap,
                 version: str,
                 base_action_class=BaseActionClass):
        self.nlu = nlu
        self.flow_map = flow_map

        self.version = version

        self._create_action_dict(base_action_class)

    def _create_action_dict(self, base_action_class):
        g = globals().copy()
        action_classes = [cls.__name__ for cls in base_action_class.__subclasses__()]
        action_objects = [
            g[class_name](self.flow_map.entities_list, self.flow_map.intents_list, self.flow_map.slots_list) for
            class_name in action_classes]

        self.action_dict = {
            cls.name(): cls for cls in action_objects
        }

    def translate_user_input(self, user_input: str, user_state: ConversationState):
        sentences = [user_input]
        predicted_output = self.nlu.predict(sentences)[0]

        intent = dict(name=predicted_output["intent"],
                      intent_ranking=predicted_output["intent_ranking"])

        if intent["name"] not in self.flow_map.actions_map.keys():
            intent["name"] = "default"
            intent["priority"] = 0

        else:
            intent["priority"] = self.flow_map.actions_map[intent["name"]].priority

        entities = predicted_output["entities"]

        user_state.intent = intent
        user_state.entities = entities

    def handle_flow(self, user_state: ConversationState, trigger_intent: str = None, request_slot: str = None, action: str = None) -> EventOutput:
        if action:
            target_action = self.action_dict[action]
            events = target_action(user_state.intent, user_state.entities, user_state.slots)

            return events

        elif trigger_intent:
            user_state.intent = dict(name=trigger_intent, intent_ranking=dict())
            user_state.entities = []

            events = self.flow_map.actions_map[trigger_intent](user_state.intent, user_state.entities, user_state.slots)
            return events

        elif request_slot:
            events = self.flow_map.requests_map[request_slot](user_state.intent, user_state.entities, user_state.slots)

            return events

        else:
            events = self.flow_map.actions_map[user_state.intent["name"]](user_state.intent, user_state.entities, user_state.slots)
            return events

    def __call__(self, user_state: ConversationState, user_message: str = None) -> MessageOutput:

        if user_state.loop_stack >= 10:
            user_state.events = EventOutput(dict(trigger_intent="default"))

        if user_state.button is not None:
            target_event = None
            for key, value in user_state.button.items():
                if user_message.lower() == key.lower():
                    target_event = value

            if target_event is not None:
                if isinstance(target_event, dict):
                    target_event = ButtonTrigger(target_event, self.flow_map.entities_list, self.flow_map.intents_list, self.flow_map.slots_list)

                target_events = target_event(user_state.intent, user_state.entities, user_state.slots)

                user_state.events = target_events
                user_state.button = None
                user_state.loop_stack += 1

        if user_message:
            self.translate_user_input(user_input=user_message, user_state=user_state)

        events = user_state.events.__dict__

        if events.get('action', None) is not None:
            user_state.events = self.handle_flow(action=events.get("action"), user_state=user_state)
            user_state.loop_stack += 1

            return self.__call__(user_state=user_state)

        if events.get("set_slot", None) is not None:
            user_state.slots.update(events.get("set_slot"))

        if events.get('text', None) is not None:
            user_state.loop_stack = 0

            output = MessageOutput(text=events.get("text"))

            del user_state.events.__dict__["text"]
            user_state.response = output

            return output

        elif events.get("button", None) is not None:
            user_state.loop_stack = 0

            button = events.get("button")
            text = button.get("text")
            events_map = button.get("events_map")

            # for key, value in button["events_map"].items():
            #     button["events_map"][key] = value.export()

            option = [key for key in events_map.keys()]

            user_state.button = events_map

            output = MessageOutput(text=text, button=option)

            del user_state.events.__dict__["button"]
            user_state.response = output

            return output

        if events.get("trigger_intent", None) is not None:
            user_state.loop_stack += 1
            user_state.events = self.handle_flow(user_state=user_state, trigger_intent=events.get("trigger_intent"))

            return self.__call__(user_state=user_state)

        if events.get("request_slot", None) is not None or user_state.slots.get("request_slot", None) is not None:
            request_slot = events.get("request_slot", None)
            if request_slot is None:
                request_slot = user_state.slots.get('request_slot')

            user_state.loop_stack += 1
            user_state.events = self.handle_flow(user_state=user_state, request_slot=request_slot)

            return self.__call__(user_state=user_state)

        user_state.events = self.handle_flow(user_state=user_state)
        return self.__call__(user_state=user_state)


class UserConversations:
    def __init__(self, db: str, entities_list: List[str], intents_list: List[str], slots_list: List[str], user_limit: int = 100, version: str = "v0.0"):
        self.db = ChatStateDB(db)
        self.entities_list = entities_list
        self.intents_list = intents_list
        self.slots_list = slots_list
        self.user_limit = user_limit
        self.user_queue = dict()
        self.frequency_queue = list()
        self.version = version

        self._load_from_db()

    def _load_from_db(self):
        messages = self.db.fetch_users()
        for value in messages:
            self.user_queue[value["user_id"]] = ConversationState(
                                                    user_id=value["user_id"],
                                                    version=value["version"],
                                                    entities_list=self.entities_list,
                                                    intents_list=self.intents_list,
                                                    slots_list=self.slots_list,
                                                    intent=value["intent"],
                                                    entities=value["entities"],
                                                    slots=value["slots"],
                                                    button=value["button"],
                                                    events=value["events"],
                                                    loop_stack=value["loop_stack"],
                                                    response=value["response"]
                                                )

            self.frequency_queue.append(dict(user_id=value["user_id"], frequency=0))

    def save_to_db(self, user_id: str):
        if self.user_queue.get(user_id, None) is not None:
            save_dict = self.user_queue[user_id].export()
            self.db.insert_table(
                **save_dict
            )

        else:
            warnings.warn(f"user {user_id} not in user_queue")

    def load_user(self, user_id: str):
        if self.user_queue.get(user_id, None) is not None:
            warnings.warn(f"user {user_id} already in user_queue")

        else:
            if len(self.user_queue.keys()) >= self.user_limit:
                self.frequency_queue = sorted(self.frequency_queue, key=lambda x: x["frequency"])

                select_user_id = self.frequency_queue[0]["user_id"]
                del self.frequency_queue[0]
                del self.user_queue[select_user_id]

            user_data = self.db.fetch_chat_state(user_id=user_id)
            if user_data is not None:
                self.user_queue[user_id] = ConversationState(
                                                        user_id=user_data["user_id"],
                                                        version=user_data["version"],
                                                        entities_list=self.entities_list,
                                                        intents_list=self.intents_list,
                                                        slots_list=self.slots_list,
                                                        intent=user_data["intent"],
                                                        entities=user_data["entities"],
                                                        slots=user_data["slots"],
                                                        button=user_data["button"],
                                                        events=user_data["events"],
                                                        loop_stack=user_data["loop_stack"],
                                                        response=user_data["response"]
                                                    )

            else:
                self.user_queue[user_id] = ConversationState(
                                                        user_id=user_id,
                                                        version=self.version,
                                                        entities_list=self.entities_list,
                                                        intents_list=self.intents_list,
                                                        slots_list=self.slots_list
                                                    )

            self.frequency_queue.append(dict(user_id=user_id, frequency=0))

    def __call__(self, user_id: str):
        user_state = self.user_queue.get(user_id, None)

        if not user_state:
            self.load_user(user_id=user_id)

            user_state = self.user_queue.get(user_id, None)

        for index, user in enumerate(self.frequency_queue):
            if user["user_id"] == user_id:
                self.frequency_queue[index]["frequency"] += 1
                break

        return user_state
