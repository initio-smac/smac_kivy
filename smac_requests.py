import socket

from kivy.app import App
import asyncio

from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from plyer import notification

try:
    import urequests as requests
except:
    #import requests
    pass

import time
import json

# server address
SMAC_SERVER = "https://smacsystem.com/smacapi/"
# default http headers
REQ_HEADERS = {'Accept': 'application/json',
               'content-type': 'application/json'
               }
RES_DATA ={}

class SmacRest():
    request = None

    # get smac_password to authorize smac requests
    def get_password(self, username):
        try:
            print(username)
            #print(datetime.now(tz=timezone.utc))
            dt = int(time.time())
            du = 50
            password = dt - du

            print(password)
            return str(password)
        except Exception as e:
            print("get password err: {}".format(e) )

    # request success callback
    def on_req_success(self, req, data):
        app = App.get_running_app()
        print("UTL", req.url)
        try:
            if req.url == SMAC_SERVER + "request_device_uid":
                print("GOT ID_DEVICE", data)
                app.update_config_variable(key="ID_DEVICE", value=data["id_device"] )
                app.load_app_data()
            elif req.url == SMAC_SERVER + "request_send_pin":
                pass
            elif req.url == SMAC_SERVER + "request_verify_pin":
                app.open_modalInfo(title="Info", text="PIN Verified Successfully.\nLogin To Continue")
        except Exception as e:
            print("ERR", e)

    # close the app
    def close_app(self, *args):
        app = App.get_running_app()
        app.stop()

    # request failure callback
    def on_req_failure(self, req, data):
        print(data)
        print(req.url)
        app = App.get_running_app()
        try:
            if req.url == SMAC_SERVER + "request_send_pin":
                pass
            elif req.url == SMAC_SERVER + "request_verify_pin":
                pass
            elif req.url == SMAC_SERVER + "request_device_uid":
                Clock.schedule_once(self.close_app, 5)
                t = "  Error while getting Device ID.\n Check your connection and try again."
                app.open_modalInfo(title="Info", text=t)
                notification.notify(message="No network. Closing App..", toast=True)
            else:
                if type(data) == socket.gaierror:
                    t = "Network Error.\nCheck Network Settings."
                    app.open_modalInfo(title="Info", text=t)
                elif type(data) == dict:
                    app.open_modalInfo(title="Info", text=data["error"])
        except Exception as e:
            print(e)

    # restapi call
    def rest_call(self, url, method, request, data={}, headers=REQ_HEADERS, on_success=None, on_failure=None):
        app = App.get_running_app()
        self.request = request
        try:
            headers = REQ_HEADERS

            if request == "request_device_uid":
                headers['Authorization'] = 'smac:smac1'
            if app.ID_DEVICE != "":
                username = app.ID_DEVICE
                password = self.get_password(username)
                headers['Authorization'] = '{}:{}'.format(username, password)

            if type(data) == dict:
                data = json.dumps(data)

            if on_success != None:
                req = UrlRequest(url=url, method=method, req_body=data, req_headers=REQ_HEADERS, on_success=on_success, on_failure=on_failure, on_error=on_failure)
            else:
                req = UrlRequest(url=url, method=method, req_body=data, req_headers=REQ_HEADERS, on_success=self.on_req_success, on_failure=self.on_req_failure, on_error=self.on_req_failure)
        except Exception as e:
            print("urequests error: {}".format(e))
            app.open_modalInfo(title="Info", text="Some error occured")

    # request device id
    def req_get_device_id(self):
        request = "request_device_uid"
        url = SMAC_SERVER + request
        self.rest_call(url=url, method="GET", request=request)

restapi = SmacRest()
