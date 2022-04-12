"""Library base file."""

import logging
import base64
import json
import requests

LOGGER = logging.getLogger(__name__)

ICLOUD_API_BASE_URL = "https://fmipmobile.icloud.com";
ICLOUD_API_URL = ICLOUD_API_BASE_URL + "/fmipservice/device/";
ICLOUD_API_COMMAND_PLAY_SOUND = "/playSound";
ICLOUD_API_COMMAND_LOST_MODE = "/lostDevice";
ICLOUD_API_COMMAND_MESSAGE = "/sendMessage"
ICLOUD_API_COMMAND_REQUEST_DATA = "/initClient";
SOCKET_TIMEOUT = 15

REQUEST_HEADERS = {
    "User-Agent" : "FindMyiPhone/500 CFNetwork/758.4.3 Darwin/15.5.0",
    "Accept-language" : "en-US",
    "X-Apple-Find-Api-Ver" : "3.0",
    "X-Apple-Authscheme" : "UserIdGuest",
    "X-Apple-Realm-Support" : "1.0",
    "Content-Type" : "application/json"
}

class findmypy_connection:

    def __init__(self, apple_id, password) -> None:
        self.authorization = base64.b64encode((apple_id+":"+password).encode("utf-8")).decode("utf-8")
        self.icloud_url_api = ICLOUD_API_URL + apple_id 


    def callAPI(self, url, payload) -> str:
        headers = REQUEST_HEADERS.copy()
        headers["authorization"] = "Basic " + self.authorization
        response = requests.post(url, data = payload, headers= headers, verify=False)
        if response.ok:
            return response.text

class findpy_manager:

    def __init__(self, connection : findpy_connection, with_family : bool) -> None:
        self.connection = connection
        self.devices = {}
        self.with_family = with_family

    def refresh_all_device(self):
        data = json.dumps(
            {
               "clientContext" : {
                    "fmly" : self.with_family,
                    "selectedDevice" : "All",
                    "shouldLocate" : True,
                    "appName" : "FindMyiPhone",
                    "appVersion" : "5.0",
                    "deviceListVersion" : 1
                }
            }
        )
        response = self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA,data)
        json_dict={}
        try:
            json_dict = json.loads(response)
        except (json.JSONDecodeError):
            print('Error')
            pass
        if "content" in json_dict:
            for device in json_dict["content"]:
                if "id" in device:
                    if device["id"] in self.devices:
                        self.devices[device["id"]].update(device)
                    else:
                        self.devices[device["id"]] = findpy_device(self,device)
        else:
            pass

    def refresh_device(self, id):
        data = json.dumps(
            {
               "clientContext" : {
                    "fmly" : self.with_family,
                    "selectedDevice" : id,
                    "shouldLocate" : True,
                    "appName" : "FindMyiPhone",
                    "appVersion" : "5.0",
                    "deviceListVersion" : 1
                }
            }
        )
        response = self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA,data)
        json_dict={}
        try:
            json_dict = json.loads(response)
        except (json.JSONDecodeError):
            print('Error')
            pass
        if "content" in json_dict:
            for device in json_dict["content"]:
                if "id" in device:
                    if device["id"] in self.devices:
                        self.devices[device["id"]].update(device)
                    else:
                        self.devices[device["id"]] = findpy_device(self,device)
        else:
            pass

    def play_sound_on_device(self, id, subject = "FindPy iPhone Alert"):
        data = json.dumps(
            {
                "device": id,
                "subject": subject,
                "clientContext": {"fmly": True},
            }
        )
        self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_PLAY_SOUND,data)     

    def display_message_on_device(self, id, subject = "FindPy iPhone Altert", message = "This is a note", sounds=False ):
        data = json.dumps(
            {
                "device": id,
                "subject": subject,
                "sound": sounds,
                "userText": True,
                "text": message,
            }
        )
        self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_PLAY_SOUND,data)  

    def set_lost_mode_on_device(self, id,  number, text = "this iPhone has been lost, Please call me.", newpasscode=""):
        data = json.dumps(
            {
                "text": text,
                "userText": True,
                "ownerNbr": number,
                "lostModeEnabled": True,
                "trackingEnabled": True,
                "device": id,
                "passcode": newpasscode
            }
        )
        self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_LOST_MODE,data)

    def init_devices_list(self):
        data = json.dumps(
            {
               "clientContext" : {
                    "fmly" : self.with_family,
                    "selectedDevice" : "All",
                    "shouldLocate" : True,
                    "appName" : "FindMyiPhone",
                    "appVersion" : "5.0",
                    "deviceListVersion" : 1
                }
            }
        )
        response = self.connection.callAPI(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA,data)
        json_dict={}

        try:
            json_dict = json.loads(response)
        except (json.JSONDecodeError):
            print('Error')
            pass
        if "content" in json_dict:
            for device in json_dict["content"]:
                if "id" in device:
                    self.devices[device["id"]] = findmypy_device(self,device)
        else:
            pass

class findmypy_device:

    def __init__(self, manager : findpy_manager, content) -> None:
        self.manager = manager
        self.content = content
        pass

    def update(self, content):
        self.content = content
        pass

    def play_sound(self, subject = "FindPy iPhone Alert"):
        self.manager.play_sound_on_device()
        

    def display_message(self, subject = "FindPy iPhone Altert", text = "This is a note", sounds=False):
        self.manager.display_message_on_device(self.content["id"],subject,text,sounds)

    def lost_mode(self, number, text = "this iPhone has been lost, Please call me.", new_passcode=""):
        self.manager.set_lost_mode_on_device(self.content["id"],number,text,new_passcode)

    def location(self):
        """Returns status information for device."""
        self.manager.refresh_all_device()
        return self.content["location"]

    def status(self, additional=[]):  
        """Returns status information for device.
        This returns only a subset of possible properties.
        """
        self.manager.refresh_all_device()
        fields = ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]
        fields += additional
        properties = {}
        for field in fields:
            properties[field] = self.content.get(field)
        return properties