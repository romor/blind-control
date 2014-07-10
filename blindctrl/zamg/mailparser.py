#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
from imapclient import IMAPClient
import email
import base64
import quopri
import re
import io



class MailParser():
    def __init__(self, config):
        self.config = config
        self._paraobservers = []
        self._csvobservers = []


    def add_csvobserver(self, observer):
        self._csvobservers.append(observer)

    def add_paraobserver(self, observer):
        self._paraobservers.append(observer)


    def parse(self):
        server = IMAPClient(self.config['EMAIL']['servername'])
        server.login(self.config['EMAIL']['username'], self.config['EMAIL']['password'])
        logging.getLogger().debug("connected to IMAP server")

        select_info = server.select_folder('INBOX')
        # get list of fitting messages
        messages = server.search(['NOT DELETED',
                                  'SUBJECT "' + self.config['EMAIL']['subject'] + '"'])
        logging.getLogger().info("%d email message(s) found" % len(messages))

        # loop through all messages
        for msgid in messages:
            # download it
            response = server.fetch(msgid, ['RFC822'])
            msg = email.message_from_string(response[msgid]['RFC822'])
            self.__process_message(msg)

        # delete messages?
        if len(messages) > 0 and int(self.config['EMAIL']['deleteAfterProcessing']):
            if int(self.config['EMAIL']['deleteAfterProcessing']) > 1:
                messages = messages[:-1]
            server.delete_messages(messages)
            if self.config['EMAIL']['expungeMailbox']:
                server.expunge()
            logging.getLogger().info("Deleted email message(s) from server")

        server.logout()


    def __process_message(self, msg):
        # some more integrity checks
        if not msg.is_multipart() or msg['subject'] != self.config['EMAIL']['subject']:
            logging.getLogger().error("invalid message detected")
            return
        logging.getLogger().info("processing email message from " + msg.get("Date"))

        # decode message body
        msg_body_qp = msg.get_payload(0).as_string()
        msg_body_qp_bytes = bytes(msg_body_qp, 'UTF-8')
        msg_body_bytes = quopri.decodestring(msg_body_qp_bytes)
        msg_body = msg_body_bytes.decode('UTF-8')

        # extract attachments
        self.__process_attachments(msg)


    def __process_attachments(self, msg):
        mail_parts = msg.get_payload()
        # remove message body, which is first part
        mail_parts[0:1] = []
        # loop through attachments
        for attachment in mail_parts:
            csv = attachment.get_payload()

            # notify listener on new data
            for observer in self._csvobservers:
                observer(csv)
