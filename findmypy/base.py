import base64
import json
import requests
import os

from findmypy.exceptions import FindMyPyApiException, FindMyPyJsonException, FindMyPyLoginException, \
    FindMyPyNoDevicesException

ICLOUD_API_BASE_URL = 'https://fmipmobile.icloud.com'
ICLOUD_API_URL = ICLOUD_API_BASE_URL + '/fmipservice/device/'
ICLOUD_API_COMMAND_REQUEST_DATA = '/initClient'
SOCKET_TIMEOUT = 15

REQUEST_HEADERS = {
    'User-Agent': 'FindMyiPhone/500 CFNetwork/758.4.3 Darwin/15.5.0',
    'Accept-language': 'en-US',
    'X-Apple-Find-Api-Ver': '3.0',
    'X-Apple-Authscheme': 'UserIdGuest',
    'X-Apple-Realm-Support': '1.0',
    'Content-Type': 'application/json'
}


class FindMyPyConnection:

    def __init__(self, apple_id, password):
        self.authorization = base64.b64encode((apple_id + ':' + password).encode('utf-8')).decode('utf-8')
        self.icloud_url_api = ICLOUD_API_URL + apple_id
        self.ca_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AppleCA.pem')

    def call_api(self, url, payload) -> str:
        headers = REQUEST_HEADERS.copy()
        headers['authorization'] = 'Basic ' + self.authorization
        response = requests.post(url, data=payload, headers=headers, verify=self.ca_path)
        if response.ok:
            return response.text
        elif response.status_code == 401:
            raise FindMyPyLoginException()
        else:
            raise FindMyPyApiException(response.status_code)


class FindMyPyManager:

    def __init__(self, connection: FindMyPyConnection, with_family: bool) -> None:
        self.connection = connection
        self.devices = {}
        self.with_family = with_family
        self.last_response = {}

    def refresh_all_device(self):
        data = json.dumps(
            {
                'clientContext': {
                    'fmly': self.with_family,
                    'selectedDevice': 'All',
                    'shouldLocate': True,
                    'appName': 'FindMyiPhone',
                    'appVersion': '5.0',
                    'deviceListVersion': 1
                }
            }
        )
        response = self.connection.call_api(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA, data)
        try:
            json_dict = json.loads(response)
            self.last_response = json_dict
        except (Exception,):
            raise FindMyPyJsonException('Could not load Dict from Json-Api Response')
        if 'content' in json_dict:
            for device in json_dict['content']:
                if 'id' in device:
                    if device['id'] in self.devices:
                        self.devices[device['id']].update(device)
                    else:
                        self.devices[device['id']] = FindMyPyDevice(self, device)
        else:
            raise FindMyPyNoDevicesException()

    def refresh_device(self, id_):
        data = json.dumps(
            {
                'clientContext': {
                    'fmly': self.with_family,
                    'selectedDevice': id_,
                    'shouldLocate': True,
                    'appName': 'FindMyiPhone',
                    'appVersion': '5.0',
                    'deviceListVersion': 1
                }
            }
        )
        response = self.connection.call_api(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA, data)
        try:
            json_dict = json.loads(response)
            self.last_response = json_dict
        except json.JSONDecodeError:
            raise FindMyPyJsonException('Could not load Dict from Json-Api Response')
        if 'content' in json_dict:
            for device in json_dict['content']:
                if 'id' in device:
                    if device['id'] in self.devices:
                        self.devices[device['id']].update(device)
                    else:
                        self.devices[device['id']] = FindMyPyDevice(self, device)
        else:
            raise FindMyPyNoDevicesException()

    def init_devices_list(self):
        data = json.dumps(
            {
                'clientContext': {
                    'fmly': self.with_family,
                    'selectedDevice': 'All',
                    'shouldLocate': True,
                    'appName': 'FindMyiPhone',
                    'appVersion': '5.0',
                    'deviceListVersion': 1
                }
            }
        )
        response = self.connection.call_api(self.connection.icloud_url_api + ICLOUD_API_COMMAND_REQUEST_DATA, data)

        try:
            json_dict = json.loads(response)
            self.last_response = json_dict
        except json.JSONDecodeError:
            raise FindMyPyJsonException('Could not load Dict from Json-Api Response')
        if 'content' in json_dict:
            for device in json_dict['content']:
                if 'id' in device:
                    self.devices[device['id']] = FindMyPyDevice(self, device)
        else:
            raise FindMyPyNoDevicesException


class FindMyPyDevice:

    def __init__(self, manager: FindMyPyManager, content) -> None:
        self.manager = manager
        self.content = content

    def update(self, content):
        self.content = content

    def location(self):
        """
        Returns status information for device.
        """

        self.manager.refresh_all_device()
        return self.content['location']

    def status(self, additional=None):
        """
        Returns status information for device.
        This returns only a subset of possible properties.
        """

        if additional is None:
            additional = []
        fields = ['batteryLevel', 'deviceDisplayName', 'deviceStatus', 'name']
        fields += additional
        properties = {}
        for field in fields:
            properties[field] = self.content.get(field)
        return properties
