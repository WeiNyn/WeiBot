import json
import os
import sys
from datetime import datetime
from os import path, listdir
import warnings

from typing import Dict, Any, Union, List
import yaml

sys.path.append(os.getcwd())

from config.high_level_parser import load_data, create_version, NormalScheme, WorkingTypeDependenceScheme
from app.setting.setting import Setting
from nlu_pipelines.DIETClassifier.src.data_reader.data_reader import make_dataframe


DOMAIN_CONFIG_PATH = Setting.domain_config
FLOW_CONFIG_PATH = Setting.flow_config

with open(DOMAIN_CONFIG_PATH, "r") as domain_file:
    DOMAIN = yaml.load(domain_file, Loader=yaml.FullLoader)

DEFAULT_CONFIG_PATH = Setting.default_config_path

with open(DEFAULT_CONFIG_PATH, "r") as default_config_file:
    DEFAULT_CONFIG = yaml.load(default_config_file, Loader=yaml.FullLoader)

HIGH_LEVEL_CONFIG_PATH = Setting.high_level_config_path

with open(HIGH_LEVEL_CONFIG_PATH, "r") as high_level_config_file:
    HIGH_LEVEL_CONFIG = yaml.load(high_level_config_file, Loader=yaml.FullLoader)

NLU_CONFIG_PATH = Setting.model_config

with open(NLU_CONFIG_PATH, "r") as nlu_config_file:
    NLU_CONFIG = yaml.load(nlu_config_file, Loader=yaml.FullLoader)


async def check_high_level_config(data: Dict[str, Any]):
    """
    Double-check the given configuration.

    :param data: dict() - configuration for QnA
    :param domain: dict() - the given domain
    :return: None
    """
    intents_map = data.get("intents_map", None)

    if not intents_map:
        raise ValueError(f"QnA data must have intents_map attribute")

    for intent in intents_map:
        if intent.get("text", None) is not None:
            NormalScheme(intent, intents_list=DOMAIN["intents"])()

        else:
            WorkingTypeDependenceScheme(intent, intents_list=DOMAIN["intents"])()


async def load_high_level_config():
    """
    Load the high_level_config_file

    :return: dict() - the high_level_config
    """
    try:
        config = load_data(HIGH_LEVEL_CONFIG_PATH)

    except Exception as ex:
        raise RuntimeError(f"Cannot load high_level_config_file by error {ex}")

    try:
        await check_high_level_config(data=config)
    except Exception as ex:
        raise ValueError(f"The high-level config is not valid by error {ex}")

    return config


async def write_high_level_config(data: Dict[str, Any]):
    """
    Write the high_level_config to file

    :param data: dict() - high_level_config data
    :return: None
    """
    try:
        await check_high_level_config(data)

    except Exception as ex:
        raise ValueError(f"Given QnA format is not valid by error {ex}")

    try:
        f = open(HIGH_LEVEL_CONFIG_PATH, "w")
        yaml.dump(data, f, sort_keys=False)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot save config to file {HIGH_LEVEL_CONFIG_PATH} by error {ex}")

    global HIGH_LEVEL_CONFIG
    HIGH_LEVEL_CONFIG = load_high_level_config()


async def load_domain():
    """
    Load the domain

    :return: dict() - the domain configuration
    """
    try:
        config = load_data(DOMAIN_CONFIG_PATH)
    except Exception as ex:
        raise RuntimeError(f"Cannot read config from {DOMAIN_CONFIG_PATH} by error {ex}")

    return config


async def write_domain(data: Dict[str, Any]):
    """
    Write the domain configuration to file

    :param data: dict() - domain configuration
    :return: None
    """
    try:
        f = open(DOMAIN_CONFIG_PATH, "w")
        yaml.dump(data, f, sort_keys=False)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot write domain to file {DOMAIN_CONFIG_PATH} by error {ex}")

    global DOMAIN
    DOMAIN = load_domain()


async def load_model_config():
    """
    Load the nlu configuration

    :return: dict() - nlu configuration
    """
    try:
        config = load_data(NLU_CONFIG_PATH)

    except Exception as ex:
        raise RuntimeError(f"Cannot read nlu_config from file {NLU_CONFIG_PATH} by error {ex}")

    return config


async def write_model_config(data: Dict[str, Any]):
    """
    Write nlu configuration to file

    :param data: dict() - nlu configuration
    :return: None
    """
    try:
        f = open(NLU_CONFIG_PATH, "w")
        yaml.dump(data, f, sort_keys=False)
        f.close()

    except Exception as ex:
        raise RuntimeError(f"Cannot write model config to file {NLU_CONFIG_PATH} by error {ex}")

    global NLU_CONFIG
    NLU_CONFIG = load_model_config()


async def add_high_level_config(intent: Dict[str, Any]):
    """
    Add QnA pair

    :param intent: dict() - the configuration for new QnA
    :return: None
    """
    global HIGH_LEVEL_CONFIG

    high_level_config = HIGH_LEVEL_CONFIG.copy()
    dup_flag = False
    for index, intent_map in enumerate(high_level_config["intents_map"]):
        if intent_map.get("intent", None) == intent.get("intent"):
            high_level_config["intents_map"][index] = intent
            dup_flag = True
            break

    if not dup_flag:
        high_level_config["intents_map"].append(intent)

    if not dup_flag:
        global DOMAIN

        domain = DOMAIN.copy()
        intents_list = domain.get("intents", [])
        intent_name = intent.get('intent', None)
        if intent_name not in intents_list:
            intents_list.append(intent_name)

        domain["intents"] = intents_list

        global NLU_CONFIG

        nlu_config = NLU_CONFIG.copy()
        intents_list = nlu_config.get("model", {}).get("intents")
        intent_name = intent.get("intent", None)
        if intent_name not in intents_list:
            intents_list.append(intent_name)

        nlu_config["model"]["intents"] = intents_list

    try:
        await check_high_level_config(data=high_level_config)

    except Exception as ex:
        raise RuntimeError(f"QnA data is not valid by error {ex}")

    if not dup_flag:
        DOMAIN = domain
        NLU_CONFIG = nlu_config

    HIGH_LEVEL_CONFIG["intents_map"] = high_level_config["intents_map"]


async def remove_high_level_config(intent: str):
    """
    Remove QnA pair

    :param intent: str - name of intent
    :return: None
    """
    global HIGH_LEVEL_CONFIG
    high_level_config = HIGH_LEVEL_CONFIG.copy()
    intents_map = high_level_config.get("intents_map", [])
    intents_map = [intent_map for intent_map in intents_map if intent_map.get("intent") != intent]
    high_level_config["intents_map"] = intents_map

    global DOMAIN
    domain = DOMAIN.copy()
    intents_list = domain.get("intents")
    intents_list = [i for i in intents_list if i != intent]
    domain["intents"] = intents_list

    global NLU_CONFIG
    nlu_config = NLU_CONFIG.copy()
    intents_list = nlu_config.get('model', {}).get('intents')
    intents_list = [i for i in intents_list if i != intent]
    nlu_config["model"]["intents"] = intents_list

    HIGH_LEVEL_CONFIG["intents_map"] = high_level_config["intents_map"]
    DOMAIN = domain
    NLU_CONFIG = nlu_config


def remove_entities(entities_list: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Apply function for loading dataset

    :param entities_list: str/list(dict()) - entities in dataset
    :return: list(dict()) - entities after filtered
    """
    global DOMAIN

    entities = DOMAIN["entities"]

    if isinstance(entities_list, str):
        try:
            entities_list = json.loads(entities_list)
        except Exception as ex:
            raise RuntimeError(f"Cannot convert entity {entities_list} by error: {ex}")

    entities_list = [entity for entity in entities_list if entity["entity_name"] in entities]

    return entities_list


def load_dataset():
    """
    Load dataset from Setting.dataset_folder

    :return: dict() - the dataset
    """
    global NLU_CONFIG

    dataset_folder = NLU_CONFIG["model"]["dataset_folder"]
    exclude_file = NLU_CONFIG["model"]["exclude_file"]
    if not exclude_file:
        exclude_file = []

    if not path.exists(dataset_folder):
        raise ValueError(f"folder {dataset_folder} does not exist")

    files_list = [path.join(dataset_folder, f) for f in listdir(dataset_folder) if path.isfile(path.join(dataset_folder, f)) and f.endswith(".yml")]

    files_list = [f for f in files_list if f not in [path.join(dataset_folder, ex) for ex in exclude_file]]

    df, _, _, _ = make_dataframe(files=files_list)

    intents = DOMAIN["intents"]

    df = df[df["intent"].isin(intents)]

    df["entities"] = df["entities"].apply(remove_entities)

    dataset: Dict[str, Any] = dict()

    for _, row in df.iterrows():
        intent = row["intent"]
        example = row["example"]
        entities = row["entities"]

        dataset[intent] = dataset.get(intent, [])
        dataset[intent].append(dict(
            text=example,
            entities=entities
        ))

    return dataset


DATASET = load_dataset()


async def change_dataset(intent_name: str, examples: List[Dict[str, Any]]):
    """
    modify the dataset

    :param intent_name: str - name of intent
    :param examples: list(dict) - examples of intent
    :return: NOne
    """
    global DOMAIN
    global NLU_CONFIG
    global DATASET

    intent_list = DOMAIN["intents"]

    if intent_name not in intent_list:
        DOMAIN["intents"].append(intent_name)
        NLU_CONFIG["model"]["intents"].append(intent_name)

    for example in examples:
        entities = example.get("entities")
        for ent in entities:
            entity_name = ent.get("entity_name", None)
            if not entity_name:
                warnings.warn(f"entity_name must be specified, ignore the {entity_name} entity_name")

            else:
                if entity_name not in DOMAIN["entities"]:
                    DOMAIN["entities"].append(entity_name)

                if entity_name not in NLU_CONFIG["model"]["entities"]:
                    NLU_CONFIG["model"]["entities"].append(entity_name)

    DATASET[intent_name] = examples

    return DATASET


async def remove_dataset(intent_name: str):
    """
    Remove an entity from dataset

    :param intent_name: str - entity name
    :return: None
    """
    global DOMAIN
    global NLU_CONFIG
    global DATASET

    if intent_name in DOMAIN["intents"]:
        DOMAIN["intents"].remove(intent_name)

    if intent_name in NLU_CONFIG["model"]["intents"]:
        NLU_CONFIG["model"]["intents"].remove(intent_name)

    if DATASET.get(intent_name, None) is not None:
        del DATASET[intent_name]


async def convert_examples(examples: List[Dict[str, Any]]) -> str:
    """
    Convert example to the string format for saving

    :param examples: list(dict) - examples in original format
    :return: str - string format for examples
    """
    output = ""
    for example in examples:
        text = example.get('text', None)
        entities = example.get('entities', None)
        entities.sort(key=lambda x: -x["position"][1])
        for entity in entities:
            entity_name = entity.get("entity_name", None)
            if not entity_name:
                continue

            entity_value = entity.get("entity", None)
            if not entity_value:
                continue

            position = entity.get("position", None)
            if not position:
                continue

            if position[0] < 0 or position[1] > len(text):
                continue

            synonym = entity.get('synonym', None)
            if not synonym:
                entity_text = """[{0}]({1})""".format(entity_value, entity_name)

            else:
                entity_text = f"[{entity_value}]" \
                              + '{"entity": "'\
                              + entity_name\
                              + '", "value": "'\
                              + synonym + '"}'

            text = text[:position[0]] + entity_text + text[position[1]:]

        output += f"- {text}\n"

    return output


async def save_dataset(folder_name: str = None):
    """
    Save dataset to folder, each intent in difference files

    :param folder_name: str - name of saving folder
    :return: None
    """
    if not folder_name:
        folder_name = f"dataset_{datetime.today().timestamp()}/"

    else:
        if not folder_name.endswith("/"):
            folder_name = f"{folder_name}/"

    base_dir = "/home/weinyn/Documents/WeiBot/dataset/"
    dataset_dir = os.path.join(base_dir, folder_name)

    if os.path.isdir(dataset_dir):
        raise ValueError(f"folder {dataset_dir} is already exists")

    os.mkdir(dataset_dir)

    global NLU_CONFIG
    global DATASET

    NLU_CONFIG["model"]["dataset_folder"] = dataset_dir

    for intent_name, examples in DATASET.items():
        data_file = dict(
            nlu=[
                dict(
                    intent=intent_name,
                    examples=await convert_examples(examples)
                )
            ]
        )

        data_file_name = f"{intent_name}.yml"
        data_file_path = os.path.join(dataset_dir, data_file_name)

        try:
            f = open(data_file_path, "w")
            yaml.dump(data_file, f, sort_keys=False)
            f.close()

        except Exception as ex:
            raise RuntimeError(f"Cannot save dataset into {dataset_dir}/{data_file_name} by error {ex}")


async def add_qna(intent: Dict[str, Any], examples: List[Dict[str, Any]]):
    """
    Add an QnA pair

    :param intent: str - name of intent
    :param examples: list(dict) - the examples for intent training dataset
    :return:
    """
    intent_name = intent.get("intent", None)
    if intent is None:
        raise ValueError(f"intent name is must be not None")

    await add_high_level_config(intent=intent)
    await change_dataset(intent_name=intent_name, examples=examples)


async def remove_qna(intent_name: str):
    """
    Remove an QnA pair

    :param intent_name: str - name of intent
    :return: None
    """
    await remove_high_level_config(intent=intent_name)
    await remove_dataset(intent_name=intent_name)


async def save_qna(dataset_folder: str):
    """
    Save config to local file

    :param dataset_folder: str - folder to save dataset
    :return: None
    """
    await save_dataset(dataset_folder)

    global HIGH_LEVEL_CONFIG
    global DOMAIN
    global NLU_CONFIG

    await write_high_level_config(data=HIGH_LEVEL_CONFIG)
    await write_domain(data=DOMAIN)
    await write_model_config(data=NLU_CONFIG)

    create_version(nlu_config=NLU_CONFIG_PATH, high_level_config=HIGH_LEVEL_CONFIG_PATH, save_file=FLOW_CONFIG_PATH)

