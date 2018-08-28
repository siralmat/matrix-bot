#!/usr/bin/env python3
import configparser
import inspect
import json
import logging
import re
import time

import requests

from bs4 import BeautifulSoup
from matrix_client.api import MatrixRequestError
from matrix_client.client import MatrixClient
# from matrix_client.crypto.olm_device import OlmDevice
from matrix_client.room import Room

from matrix_bot.modules.base import MatrixBotModule
from matrix_bot import modules

class MatrixBot:
    def __init__(self, config):
        self.config = config
        self.modules = []

        for key, value in modules.__dict__.items():
            if inspect.isclass(value) and issubclass(value, MatrixBotModule):
                m = value.create(config)
                if m:
                    self.modules.append(m)


    def run(self):
        pass


    def on_event(self, event):
        print(event)
        if event['type'] == 'm.room.message':
            self.on_room_message(room_id=event['room_id'],
                                 sender_id=event['sender'],
                                 content=event['content'],
                                 event=event)

        for module in self.modules:
            module.process(self.client, event)


    def on_room_message(self, room_id, sender_id, content, event):
        pass


    def on_invite(self, room_id, event):
        self.client.join_room(room_id)


    def run(self):
        base_url = self.config['main']['base_url']
        user_id = self.config['main']['user_id']
        password = self.config['main']['password']
        device_id = self.config['main']['device_id']

        self.client = MatrixClient(base_url=base_url)
        self.client.login(user_id, password, device_id=device_id)
        # olm_device = OlmDevice.load_or_create_olm_device(cli.api, user_id, device_id)
        # sessions = olm_device.create_outbound_sessions_to_user("@thi:matrix.thialfihar.org")

        # def get_first_session(d):
        #     return get_first_session(list(d.values())[0]) if isinstance(d, dict) else d

        # outbound_session = get_first_session(sessions)

        # olm_device.send_encrypted_message_to_session(
        #     "#tmi:matrix.thialfihar.org", outbound_session, 'Hello!')

        self.client.add_invite_listener(self.on_invite)
        self.client.add_listener(self.on_event)
        self.client.start_listener_thread()

        while True:
            time.sleep(0.5)