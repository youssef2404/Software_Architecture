import threading
import time
import traceback

from src.Environnement.VariablesControl import VariablesControl
from src.Utilities.Logger import Logger
from opcua import Client, ua


class OpcUaClient(threading.Thread):
    def __init__(self, address=None, port=None, opc_url=None,
                 related_edge_box=None, username=None, password=None):

        super(OpcUaClient, self).__init__()

        if related_edge_box is not None:
            self.related_edge_box = related_edge_box
            self.logger = self.related_edge_box.logger

        else:

            self.logger = Logger(log_file_name="OPC_UA_Client_Log.log",
                                 log_level="INFO", is_printing=True)

        try:
            if opc_url is None:
                self.address = address
                self.port = port
                self.url = "opc.tcp://{}:{}".format(self.address, self.port)
            else:
                self.url = opc_url

            self.username = username
            self.password = password

            self.client = Client(url=self.url)

            try:
                if self.username is not None and self.password is not None:
                    self.client.set_user(self.username)
                    self.client.set_password(self.password)

            except Exception:
                self.logger.error(traceback.format_exc())
                self.logger.error("wrong username or password")

            self.subscription_list = []
            self.subscription_handler_list = []
            self.connected = False
            try:

                self.client.connect()
                self.connected = True

            except Exception:
                self.connected = False
                self.logger.error(traceback.format_exc())
                return

            self.running = False

        except Exception:
            self.logger.error(traceback.format_exc())

    def reconnect(self):
        while not self.connected:
            try:
                self.client.connect()
                self.connected = True
                self.logger.info("reconnected to opc server")

                for handler in self.subscription_handler_list:
                    handler = self.subscription_handler_list.pop(0)

                    self.subscribe(node_id=handler.node_id,
                                   rising_function=handler.rising_function,
                                   falling_function=handler.falling_function,
                                   changed_value=handler.changed_value)

                    self.logger.debug("resubscribed to {} on opc server {}".format(handler.node_id, self.url))

            except Exception:
                self.logger.error(traceback.format_exc())
                self.logger.error("error connecting to opc server {}".format(self.url))
                reconnect_time = VariablesControl.time_to_reconnect.value
                self.logger.error("waiting {} sec to reconnect".format(reconnect_time))
                self.connected = False
                time.sleep(reconnect_time)

    def run(self):
        self.running = True
        while self.running:

            try:
                self.client.get_endpoints()
                time.sleep(1)
                self.connected = True

            except Exception:
                self.connected = False

            self.reconnect()

    def subscribe(self, node_id, rising_function=(lambda *args, **kwargs: None),
                  falling_function=(lambda *args, **kwargs: None),
                  changed_value=(lambda *args, **kwargs: None)):

        node_obj = self.client.get_node(nodeid=node_id)
        handler = SubscriptionHandler(rising_function, falling_function, changed_value, opc_client=self,
                                      node_id=node_id)
        try:
            subscription = self.client.create_subscription(10, handler)
            subscription.subscribe_data_change(node_obj)

        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error("error subscribing to node {} on server {}".format(node_id, self.url))
            subscription = None

        self.subscription_list.append(subscription)
        self.subscription_handler_list.append(handler)
        return handler, subscription

    def write(self, node_id, value, variant_type):
        node_obj = self.client.get_node(nodeid=node_id)
        node_obj.set_value(ua.DataValue(ua.Variant(value, variant_type)))

        del node_obj

    def read(self, node_id):
        node_obj = self.client.get_node(nodeid=node_id)
        value = node_obj.get_value()
        return value

    def unsubscribe(self, subscription, handle=None):
        subscription.unsubscribe(handle)
        subscription.delete()

    def kill(self):
        self.running = False


class SubscriptionHandler(object):

    def __init__(self, rising_function=None, falling_function=None, changed_value=None, opc_client=None,
                 node_id=''):

        self.opc_client = opc_client
        self.node_id = node_id

        self.rising_function = self.default_function
        self.falling_function = self.default_function
        self.changed_value = self.default_function

        if callable(rising_function):
            self.rising_function = rising_function

        if callable(falling_function):
            self.falling_function = falling_function

        if callable(changed_value):
            self.changed_value = changed_value

    def datachange_notification(self, node, val, data):

        if type(val) == bool:
            if val:
                self.rising_function(data=data, val=val, node=node, opc_client=self.opc_client)
            else:
                self.falling_function(data=data, val=val, node=node, opc_client=self.opc_client)
        else:
            self.changed_value(data=data, val=val, node=node, opc_client=self.opc_client)

    def event_notification(self, event):
        pass

    def default_function(self, data, val, node, opc_client):
        return
