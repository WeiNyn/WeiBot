from typing import Union, Dict, Any, List
import yaml
from parsers.mapping import ActionMap, RequestMap


class FlowMap:
    """
    FlowMap that contains the logic config for every action_map and request_map
    """
    def __init__(self, flow_config: Union[Dict[str, Any], str], domain: Union[Dict[str, Any], str]):
        """
        Create flow_map based on the flow_config and domain (contains all available intents, entities and slots)
        :param flow_config: union(dict, file_path) - the config in dictionary format or the path to the config file
        :param domain: union(dict, file_path) - the domain in dictionary format or the path to the domain
        """
        self.flow_config = flow_config
        self.domain = domain

        if isinstance(flow_config, str):
            try:
                f = open(flow_config, "r")
                flow_config = yaml.load(f, Loader=yaml.FullLoader)
                f.close()

            except Exception as ex:
                raise RuntimeError(f"Cannot import config from file {flow_config} by error: {ex}")

        if isinstance(domain, str):
            try:
                f = open(domain, "r")
                domain = yaml.load(f, Loader=yaml.FullLoader)
                f.close()

            except Exception as ex:
                raise RuntimeError(f"Cannot import domain from file {domain} by error: {ex}")

        self.entities_list: List[str] = domain["entities"]
        for entity in self.entities_list:
            if not isinstance(entity, str):
                raise ValueError(f"all entity must be a string, not {entity}: {type(entity)}")

        self.intents_list: List[str] = domain["intents"]
        for intent in self.intents_list:
            if not isinstance(intent, str):
                raise ValueError(f"all intent must be a string, not {intent}: {type(intent)}")

        self.slots_list: List[str] = domain["slots"]
        for slot in self.slots_list:
            if not isinstance(slot, str):
                raise ValueError(f"all slot must be a string, not {slot}: {type(slot)}")

        self.actions_map: Dict[str, ActionMap] = {}
        for intent in flow_config["actions_map"]:
            action_map = ActionMap(intent, self.entities_list, self.intents_list, self.slots_list)
            self.actions_map[action_map.intent] = action_map

        self.requests_map: Dict[str, RequestMap] = {}
        for slot in flow_config["requests_map"]:
            request_map = RequestMap(slot, self.entities_list, self.intents_list, self.slots_list)
            self.requests_map[request_map.slot] = request_map

    def export(self):
        """
        Export to the convertible dictionaries for config and domain
        :return: dict()
        """
        flow_config = dict()
        flow_config["actions_map"] = [action_map.export() for action_map in self.actions_map.values()]
        flow_config["requests_map"] = [request_map.export() for request_map in self.requests_map.values()]

        domain = dict(
            intents=self.intents_list,
            entities=self.entities_list,
            slots=self.slots_list
        )

        return flow_config, domain

