from actions.actions import BaseActionClass

class Setting:
    model_config = "/home/weinyn/Documents/WeiBot/config/config.yml"
    flow_config = "/home/weinyn/Documents/WeiBot/config/final_config.yml"
    domain_config = "/home/weinyn/Documents/WeiBot/config/domain.yml"

    app_id = "c072edf3-5800-4c7b-939a-107508981bf0"
    app_password = "~gKRJs8q..l32CgS-4WD84Zej-Dl8.p5bo"
    bot = {
        "id": "28:c072edf3-5800-4c7b-939a-107508981bf0",
        "name": "CLeVer"
    }

    user_db = "database/test_db.db"

    version = "v0.0"

    base_action_class = BaseActionClass

    arm_on = True
    arm_socket = "http://10.0.0.100:8088"
    host_link = "https://6d7fdc5abf76.ap.ngrok.io"
    images_path = "/home/weinyn/Documents/WeiBot/app/images"

    default_config_path = "/home/weinyn/Documents/WeiBot/config/default_config.yml"
    high_level_config_path = "/home/weinyn/Documents/WeiBot/config/high_level_config.yml"
    config_path = "/home/weinyn/Documents/WeiBot/config/"

