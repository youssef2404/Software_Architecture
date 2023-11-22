import traceback
from pathlib import Path
from threading import Thread

import redis

from src.Utilities.Logger import Logger


class RedisHandler:

    def __init__(self, redis_host, redis_port, redis_db, redis_password, parent_class):

        self.__redis_host = redis_host
        self.__redis_port = redis_port
        self.__redis_db = redis_db
        self.__redis_password = redis_password

        self.__redis = None
        self.__redis_subscriber = None

        self.logger = parent_class.logger

    def redis_connect(self):
        try:

            self.__redis = redis.Redis(host=str(self.__redis_host), port=int(str(self.__redis_port)),
                                       db=int(str(self.__redis_db)), password=str(self.__redis_password))

            return self.ping()

        except Exception:
            self.logger.error(traceback.format_exc())

    def subscribe_to_specific_topic(self, topic_to_subscribe):
        try:

            self.__redis_subscriber = self.__redis.pubsub()
            self.__redis_subscriber.subscribe(topic_to_subscribe)

        except Exception:
            self.logger.error(traceback.format_exc())

    def publish_message(self, topic_to_publish, message, on_failing_function=(lambda *args, **kwargs: None)):
        try:
            num_clients = self.__redis.publish(channel=topic_to_publish, message=message)

            if num_clients > 0:

                return True

            else:

                return False

        except redis.exceptions.ConnectionError:

            self.logger.error(traceback.format_exc())

            try:

                on_failing_function(message)

            except TypeError:

                self.logger.error(traceback.format_exc(limit=1))

            except Exception:

                self.logger.error(traceback.format_exc())

        except Exception:

            self.logger.error(traceback.format_exc())

    def redis_read_message(self, on_message_bind_function):
        try:

            for message in self.__redis_subscriber.listen():

                if message['type'] == 'message':

                    msg = message['data'].decode('utf-8')

                    if on_message_bind_function(msg) is not None and callable(on_message_bind_function(msg)):
                        on_message_bind_function(msg)

        except Exception:

            self.logger.error(traceback.format_exc())

    def bind_consumer_to_function(self, on_message_bind_function):
        try:

            bound_function_thread = Thread(target=self.redis_read_message,
                                           kwargs={
                                               'on_message_bind_function': on_message_bind_function})

            bound_function_thread.start()

        except Exception:

            self.logger.error(traceback.format_exc())

    def ping(self):

        try:

            return self.__redis.ping

        except Exception:

            self.logger.error(traceback.format_exc())

    def unsubscribe_from_specific_topic(self, topic_to_unsubscribe):

        try:

            self.__redis_subscriber.unsubscribe(topic_to_unsubscribe)

        except Exception:

            self.logger.error(traceback.format_exc())

    def publish_list(self, topic_to_publish, list_of_messages: list):

        try:

            for message in list_of_messages:
                self.__redis.publish(channel=topic_to_publish, message=message)

        except Exception:

            self.logger.error(traceback.format_exc())

    def redis_disconnect(self):

        try:

            self.__redis.disconnect()

            return self.ping()

        except Exception:
            self.logger.error(traceback.format_exc())
