# Author: Roman Morawek <roman.morawek@embyt.com>

import logging
import urllib.request
import ssl
import base64
import json


class HttpClient():
    def __init__(self, url, password):
        self.url = url
        credentials = "operator:{}".format(password).encode()
        encoded_credentials = base64.b64encode(credentials)
        authorization = b'Basic ' + encoded_credentials
        self.http_headers = {
            'Content-Type': 'application/json',
            'Authorization': authorization,
        }
        # ignore ssl certificate errors
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def read(self, opc_tags, callback=None, callback_arguments=None, error_callback=None):
        # convert potential single tag to array
        if type(opc_tags) is not list:
            opc_tags = [opc_tags]

        # build opc item query string
        read_items = opc_tags
        json_body = {
            "Options": {
                "ClientRequestHandle": "HttpClient",
            },
            "Read": read_items,
        }

        # prepare SOAP request.
        request = urllib.request.Request(
            self.url, json.dumps(json_body).encode(), self.http_headers)
        result = urllib.request.urlopen(request, context=self.ctx)

        # parse result
        response = result.read()
        root = json.loads(response)
        values = root["ReadResponse"]
        # call notification handler
        # if callback is not None:
        #  callback(values, callback_arguments)
        return values

    def write(self, opc_tags, types, values, callback=None, callback_arguments=None, error_callback=None):
        # build message body
        write_items = []
        for i in range(len(opc_tags)):
            write_items.append({
                "ItemName": opc_tags[i],
                "ClientItemHandle": opc_tags[i],
                "Value": str(values[i]),
            })
        json_body = {
            "Options": {
                "ClientRequestHandle": "HttpClient",
            },
            "Write": write_items,
        }

        request = urllib.request.Request(
            self.url, json.dumps(json_body).encode(), self.http_headers)
        result = urllib.request.urlopen(request, context=self.ctx)

        # parse result
        response = result.read()
        # print(response)
        # root = json.loads(response)
