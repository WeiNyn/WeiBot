from actions.actions import BaseActionClass

class Setting:
    debug = False

    model_config = "config/config.yml"
    flow_config = "config/final_config.yml"
    domain_config = "config/domain.yml"

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
    host_link = "http://bf34aef733a4.ap.ngrok.io"
    images_path = "WeiBot/app/images"

    default_config_path = "config/default_config.yml"
    high_level_config_path = "config/high_level_config.yml"
    config_path = "config/"
    model_path = "models/"
    dataset_path = "dataset/"
