import threading
import time
import traceback

from src.Environnement.RedisTopicsEnum import RedisTopicsEnum
from src.Handlers.RedisHandler import RedisHandler

"""""
class not completed 
test upload to preprocessing
"""


class RedisPublishToPreProcessingHandler(threading.Thread):
    def __init__(self, related_edgebox):

        super(RedisPublishToPreProcessingHandler, self).__init__(name=__name__)

        self.__related_edgebox = related_edgebox
        self._related_edgebox_reference = self.__related_edgebox.get_edge_box_reference()

        self.__redis_host = self.__related_edgebox.get_redis_host()
        self.__redis_port = self.__related_edgebox.get_redis_port()
        self.__redis_db = self.__related_edgebox.get_redis_db()
        self.__redis_password = self.__related_edgebox.get_redis_password()

        self.__redis_state = None
        self.__database_connection = None
        self.__cursor = None

        self.running = False
        self.message_pile = []

        self.logger = self.__related_edgebox.logger

        self.__topic_production = RedisTopicsEnum.production_topic.value
        self.redisHandler = RedisHandler(redis_host=self.__redis_host, redis_port=self.__redis_port,
                                         redis_db=self.__redis_db, redis_password=self.__redis_password,
                                         parent_class=self)

    def run(self):

        self.running = True

        self.logger.info("started thread Publish To PreProcessing from edgebox {}".
                         format(self._related_edgebox_reference))

        self.redisHandler.redis_connect()

        while self.running:

            while self.message_pile and self.running:

                read_from_pile = self.message_pile.pop(0)

                if self.redisHandler.ping():

                    try:

                        self.redisHandler.publish_message(topic_to_publish=self.__topic_production,
                                                          message=read_from_pile,
                                                          on_failing_function=self.store_data_offline)

                    except Exception:

                        self.logger.error(traceback.format_exc())

                        self.logger.error(
                            "Error publishing from server listener, restoring message in message pile")

                        self.message_pile.insert(0, read_from_pile)
                else:

                    self.store_data_offline(message=read_from_pile)

                time.sleep(1)

    def store_data_offline(self, message):

        try:

            self.__related_edgebox.get_redis_publisher_from_offline_queue().append_message_to_queue(message=message)

        except Exception:

            self.logger.error(traceback.format_exc())

    """
    getters and setters bloc
    """

    def get_redis_host(self):
        return self.__redis_host

    def set_redis_host(self, redis_host):
        self.__redis_host = redis_host

    def get_redis_port(self):
        return self.__redis_port

    def set_redis_port(self, redis_port):
        self.__redis_port = redis_port

    def get_redis_db(self):
        return self.__redis_db

    def set_redis_db(self, redis_db):
        self.__redis_db = redis_db

    def get_redis_password(self):
        return self.__redis_password

    def set_redis_password(self, redis_password):
        self.__redis_password = redis_password
