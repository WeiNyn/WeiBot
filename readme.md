# HR Q&A Chatbot

[![N|Solid](https://cldup.com/dTxpPi9lDf.thumb.png)](https://nodesource.com/products/nsolid)

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

The source code for HR Q&A Chatbot, including

- Server for hosting chatbot through Skype
- Server for CMS backend that modify chatbot data and conversation
- Server for connecting to Blueprint chatbot, Face punch-in system

## Requirements

- FastAPI
- Uvicorn
- Torch
- socketio
- transformers

## Functions
- Intent classification and entities recognition by trainsformers
- Training on server route (the data format follow Rasa chatbot nlu format)
- Conversation flow control by using pre-defined rule that can write in key-value format in .yml file
- Database to store user conversation and actions
- Normal action that easily defined in key-value format
- Python-logical action that defined in python code
- Some ARM system related functions

## Setting

All the server setting stored in src/setting.py
Please eddit the setting file if you don't really need to modify the way the server works.
```python
from actions.actions import BaseActionClass #the base action class, all custom action must inherit this class

class Setting:
    debug = False #log the debug log or not
    
    model_config = "config/config.yml" #config for NLU model, please check the model github at https://github.com/WeiNyn/DIETClassifier-pytorch
    flow_config = "config/final_config.yml" #config for conversation flow, please check the doc at https://docs.google.com/document/d/1NBd1lGCI0-bfPmMaCLnbmCY_DQhpkR5wHM3ZXIriBSM/edit?usp=sharing
    domain_config = "config/domain.yml" #config for domain, check the nlu model github

    #this is information for bot in azure service, use your own information
    app_id = "c072edf3-5800-4c7b-939a-107508981bf0"
    app_password = "~gKRJs8q..l32CgS-4WD84Zej-Dl8.p5bo"
    bot = {
        "id": "28:c072edf3-5800-4c7b-939a-107508981bf0",
        "name": "CLeVer"
    }

    user_db = "database/test_db.db" #path to SQLite database file

    version = "v0.0"

    base_action_class = BaseActionClass

    arm_on = False #connect with ARM system or not, using the following config
    arm_socket = "http://10.0.0.100:8088"
    host_link = "http://bf34aef733a4.ap.ngrok.io"
    images_path = "WeiBot/app/images"

    default_config_path = "config/default_config.yml" #base flow config path, you can custom your own config to write the different high_level_config
    high_level_config_path = "config/high_level_config.yml" #high level config, that base on the the rule of default config
    #these folders used to store created files
    config_path = "config/" 
    model_path = "models/"
    dataset_path = "dataset/"

```
## Run server

Please install all requirements before running server

```sh
uvicorn app.main:app --port 5004 --host 0.0.0.0
```

Check the live document for API at: http://localhost:5004/docs

## Chatbot config

Please create your own bot service on Microsoft Azure service, and then put your bot _app_id_ and _password_ in the Setting.
Set the endpoint of bot service to the https link to the server:

http://[server-address]/chatbot/botframework

## Imrpovement Note

You can make a custom chatbot with new rule by changing the conversation config and put dataset for training new NLU model.

You can use ngrok to make an temporary https link to your server (re-create each time the ngrok server stop)

## For intermal use only

The RTX 3090 do not support torch at the current time, so you must install the compatible version of torch

You can use the '/HuyNguyen/venv/' environment, I installed all the necessary packages

All the route that related to CMS and ARM was confirmed and used by MR. Huy Thach, this server is backend for these application.

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [dill]: <https://github.com/joemccann/dillinger>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [john gruber]: <http://daringfireball.net>
   [df1]: <http://daringfireball.net/projects/markdown/>
   [markdown-it]: <https://github.com/markdown-it/markdown-it>
   [Ace Editor]: <http://ace.ajax.org>
   [node.js]: <http://nodejs.org>
   [Twitter Bootstrap]: <http://twitter.github.com/bootstrap/>
   [jQuery]: <http://jquery.com>
   [@tjholowaychuk]: <http://twitter.com/tjholowaychuk>
   [express]: <http://expressjs.com>
   [AngularJS]: <http://angularjs.org>
   [Gulp]: <http://gulpjs.com>

   [PlDb]: <https://github.com/joemccann/dillinger/tree/master/plugins/dropbox/README.md>
   [PlGh]: <https://github.com/joemccann/dillinger/tree/master/plugins/github/README.md>
   [PlGd]: <https://github.com/joemccann/dillinger/tree/master/plugins/googledrive/README.md>
   [PlOd]: <https://github.com/joemccann/dillinger/tree/master/plugins/onedrive/README.md>
   [PlMe]: <https://github.com/joemccann/dillinger/tree/master/plugins/medium/README.md>
   [PlGa]: <https://github.com/RahulHP/dillinger/blob/master/plugins/googleanalytics/README.md>
