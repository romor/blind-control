#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import urllib.request
import base64
import xml.etree.ElementTree as ET


class OpcClient():
    SOAP_TEMPLATE_READ="""
        <?xml version="1.0" encoding="utf-8"?>
    	<soap:Envelope
    		xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    		xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    		xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    		<soap:Body>
    			<Read xmlns="http://opcfoundation.org/webservices/XMLDA/1.0/">
    			  <Options ClientRequestHandle="js" LocaleID="en-US" />
    			  <ItemList MaxAge="0">
    				{items}
    			  </ItemList>
    			</Read>
    		</soap:Body>
    	</soap:Envelope>
    """

    SOAP_TEMPLATE_WRITE="""
        <?xml version="1.0" encoding="utf-8"?>
    	<soap:Envelope
    		xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    		xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    		xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    		<soap:Body>
    			<Write xmlns="http://opcfoundation.org/webservices/XMLDA/1.0/" ReturnValuesOnReply="true">
    			  <Options ClientRequestHandle="js" LocaleID="en-US" />
    			  <ItemList>
    				{items}
    			  </ItemList>
    			</Write>
    		</soap:Body>
    	</soap:Envelope>
    """


    def __init__(self, url, password):
        self.url = url

        credentials = "operator:{}".format(password).encode()
        encoded_credentials = base64.b64encode(credentials)
        authorization = b'Basic ' + encoded_credentials
        self.http_headers = {
            'Content-Type': 'text/xml',
            'Authorization': authorization,
            'SOAPAction': '/DA'
        }


    def read(self, opc_tags, callback=None, callback_arguments=None, error_callback=None):
        # convert potential single tag to array
        if type(opc_tags) is not list:
            opc_tags = [ opc_tags ]

    	# build opc item query string
        opc_string = ""
        for tag in opc_tags:
            opc_string += '<Items ItemName="{}" />'.format(tag)

    	# create our SOAP body content based off of the template.
        msg_body = self.SOAP_TEMPLATE_READ.format(items=opc_string).strip()

    	# prepare SOAP request.
        request = urllib.request.Request(self.url, msg_body.encode(), self.http_headers)
        result = urllib.request.urlopen(request)

        # parse result
        response = result.read()
        root = ET.fromstring(response)
        item_list = root[0][0][1]
        values = []
        for item in item_list:
            values.append(item[0].text)

		# call notification handler
        #callback(values, callback_arguments)
        return values


    def write(self, opc_tags, types, values, callback=None, callback_arguments=None, error_callback=None):
        # build message body
        opc_string = ""
        for i in range(len(opc_tags)):
            logging.getLogger().debug("writing {}={}".format(opc_tags[i], values[i]))
            opc_string += '<Items ItemName="{tag}" ClientItemHandle="{tag}">'.format(tag=opc_tags[i])
            opc_string += '<Value xsi:type="{}">'.format(types[i])
            opc_string += str(values[i])
            opc_string += '</Value>'
            opc_string += '</Items>'
        msg_body = self.SOAP_TEMPLATE_WRITE.format(items=opc_string).strip()

        request = urllib.request.Request(self.url, msg_body.encode(), self.http_headers)
        result = urllib.request.urlopen(request)

        # parse result
        response = result.read()
        #print(response)
        root = ET.fromstring(response)
        item_list = root[0][0][1]
        values_ok = []
        for i in range(len(item_list)):
            # if the item contains a subnode (with "Value" tag) the command succeded
            if len(item_list[i]) == 0:
                logging.getLogger().error("Error writing {}.".format(opc_tags[i]))
