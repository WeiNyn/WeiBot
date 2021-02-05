from typing import Dict, Any, List

import yaml

DEFAULT_CONFIG_FILE = "config/default_config.yml"
HIGH_LEVEL_CONFIG = "config/high_level_config.yml"
DOMAIN = "config/domain.yml"


def load_data(config: str) -> Dict[str, Any]:
    try:
        f = open(config, "r")
        data = yaml.load(f, Loader=yaml.FullLoader)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot load data from {config}")

    return data


class NormalScheme:
    def __init__(self, config_dict: Dict[str, Any], intents_list: List[str]):
        self.config_dict = config_dict

        self._check(intents_list=intents_list)

    def _check(self, intents_list):
        intent = self.config_dict.get("intent", None)
        if not intent:
            raise ValueError(f"Intent must be specified")

        if intent not in intents_list:
            raise ValueError(f"intent {intent} is not an available intent")

        text = self.config_dict.get("text", None)
        if not text:
            raise ValueError(f"Text must be specified, at {intent}")

        if not isinstance(text, str):
            raise ValueError(f"Text must be a string, not {text}")

        output_dict = dict(
            intent=intent,
            set=dict(latest_question=intent),
            triggers=list([
                dict(
                    text=list([
                        text
                    ])
                )
            ])
        )

        self.output_dict = output_dict

    def export(self) -> Dict[str, Any]:
        return self.config_dict

    def __call__(self):
        return self.output_dict


class WorkingTypeDependenceScheme:
    def __init__(self, config_dict: Dict[str, Any], intents_list: List[str]):
        self.config_dict = config_dict

        self._check(intents_list)

    def _check(self, intents_list: List[str]):
        intent = self.config_dict.get("intent", None)
        if not intent:
            raise ValueError(f"Intent must be specified")

        if intent not in intents_list:
            raise ValueError(f"intent {intent} is not an available intent")

        working_type = self.config_dict.get("working_type", None)
        if not working_type:
            raise ValueError(f"working_type must be specified, at intent {intent}")

        if not isinstance(working_type, dict):
            raise ValueError(f"working_type must be dictionary, not {working_type}")

        office_hours = working_type.get("office hours", None)
        if not office_hours:
            raise ValueError(f"office hours must be specified")

        if not isinstance(office_hours, str):
            raise ValueError(f"office hours response must be string, not {office_hours}")

        shift = working_type.get("shift", None)
        shift_flow = []
        if not shift:
            raise ValueError(f"shift must be specified")

        if isinstance(shift, dict):
            day_shift = shift.get("day shift", None)
            afternoon_shift = shift.get("afternoon shift", None)
            night_shift = shift.get("night shift", None)

            if not (day_shift is not None and afternoon_shift is not None and night_shift is not None):
                raise ValueError(f"day shift, afternoon shift, night shift must be specified")

            else:
                if not (isinstance(day_shift, str), isinstance(afternoon_shift, str), isinstance(night_shift, str)):
                    raise ValueError(f"day shift, night shift must be string")

            shift_flow = [
                dict(
                    slot=dict(
                        working_type="shift",
                        shift_type="day shift"
                    ),
                    text=list([day_shift])
                ),
                dict(
                    slot=dict(
                        working_type="shift",
                        shift_type="afternoon shift"
                    ),
                    text=list([afternoon_shift])
                ),
                dict(
                    slot=dict(
                        working_type="shift",
                        shift_type="night shift"
                    ),
                    text=list([night_shift])
                ),
                dict(
                    slot=dict(
                        working_type="shift"
                    ),
                    request_slot="shift_type"
                )
            ]
        elif isinstance(shift, str):
            shift_flow = [
                dict(
                    slot=dict(
                        working_type="shift"
                    ),
                    text=list([shift])
                )
            ]

        else:
            raise ValueError(f"shift must be string or dictionary")

        output_dict = dict(
            intent=intent,
            set=dict(latest_question=intent),
            set_slot=dict(
                working_type=dict(
                    from_entity=dict(
                        working_type=True,
                        shift_type="shift"
                    )
                )
            ),
            triggers=list([
                dict(
                    slot=dict(
                        working_type="office hours"
                    ),
                    text=list([office_hours])
                )
            ]) + shift_flow + list([
                dict(
                    request_slot="working_type"
                )
            ])
        )

        self.output_dict = output_dict

    def export(self) -> Dict[str, Any]:
        return self.config_dict

    def __call__(self):
        return self.output_dict


def high_level_parser(high_level_config: str, save_file: str, default_config: str = DEFAULT_CONFIG_FILE, domain: str = DOMAIN):
    try:
        default_config = load_data(default_config)
        domain = load_data(domain)
        high_level_config = load_data(high_level_config)

    except Exception as ex:
        raise RuntimeError(f"Cannot load data from {default_config}/{domain}/{high_level_config}")

    intents_map = high_level_config["intents_map"]

    for intent in intents_map:
        if intent.get("text", None) is not None:
            default_config["actions_map"].append(NormalScheme(intent, intents_list=domain["intents"])())

        else:
            default_config["actions_map"].append(WorkingTypeDependenceScheme(intent, intents_list=domain["intents"])())

    try:
        config_file = open(save_file, "w")
        yaml.dump(default_config, config_file, sort_keys=False)
        config_file.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot save data to {save_file}")


if __name__ == "__main__":
    default_config = load_data(DEFAULT_CONFIG_FILE)
    high_level_config = load_data(HIGH_LEVEL_CONFIG)
    domain = load_data(DOMAIN)

    intents_map = high_level_config["intents_map"]

    for intent in intents_map:
        if intent.get("text", None) is not None:
            default_config["actions_map"].append(NormalScheme(intent, intents_list=domain["intents"])())

        else:
            default_config["actions_map"].append(WorkingTypeDependenceScheme(intent, intents_list=domain["intents"])())

    f = open("config/test_flow_config_from_high_level.yml", "w")
    yaml.dump(default_config, f, sort_keys=False)
    f.close()
