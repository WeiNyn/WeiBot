from typing import List, Dict, Any

import yaml


def get_intent(domain: str) -> List[str]:
    try:
        f = open(domain, "r")
        data = yaml.load(f, Loader=yaml.FullLoader)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot get intent list from {domain}")

    return data["intents"]


def flow_config_create(intent_list: List[str]) -> Dict[str, Any]:
    actions_map = []

    for intent in intent_list:
        actions_map.append(dict(
            intent=intent,
            set=None,
            set_slot=None,
            triggers=None,
        ))

    data = dict(
        actions_map=actions_map,
        requests_map=None
    )

    return data


def write_flow_config(data: Dict[str, Any], file: str):
    try:
        f = open(file, "w")
        yaml.dump(data, f, sort_keys=False)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot write flow_config to {file}")


if __name__ == "__main__":
    from datetime import datetime
    write_flow_config(flow_config_create(get_intent("config/domain.yml")), f"config/flow_config_{datetime.today().timestamp()}.yml")
