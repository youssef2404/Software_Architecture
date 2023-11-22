import threading
import time
import traceback

import persistqueue
from src.Environnement.RedisTopicsEnum import RedisTopicsEnum
from src.Handlers.RedisHandler import RedisHandler


class RedisPublishFromOfflineQueueHandler(threading.Thread):
    def __init__(self, related_edgebox):
        super(RedisPublishFromOfflineQueueHandler, self).__init__(name=__name__)

        self.__related_edgebox = related_edgebox
        self._related_edgebox_reference = self.__related_edgebox.get_edge_box_reference()

        self.running = False

        self.__redis_host = self.__related_edgebox.get_redis_host()
        self.__redis_port = self.__related_edgebox.get_redis_port()
        self.__redis_db = self.__related_edgebox.get_redis_db()
        self.__redis_password = self.__related_edgebox.get_redis_password()

        self.production_topic = RedisTopicsEnum.production_topic.value
        self.path_queue = RedisTopicsEnum.offline_queue_path.value

        self.offline_mode = True

        self.logger = self.__related_edgebox.logger

        self.redisHandler = RedisHandler(redis_host=self.__redis_host, redis_port=self.__redis_port,
                                         redis_db=self.__redis_db, redis_password=self.__redis_password,
                                         parent_class=self)

    def run(self):
        self.running = True

        self.logger.info("started thread publish from queue from edgebox {}".format(self._related_edgebox_reference))

        while self.running:
            self.publish_from_queue()

        self.logger.info("ended thread publish from queue of")

    def publish_from_queue(self):

        try:

            queue = persistqueue.SQLiteQueue(path=self.path_queue,
                                             name=self._related_edgebox_reference,
                                             auto_commit=True,
                                             multithreading=True)

            test_connection = self.redisHandler.redis_connect()

            if not queue.empty() and test_connection:
                message = queue.get()

                self.logger.info("publishing Offline message")
                self.redisHandler.publish_message(topic_to_publish=self.production_topic,
                                                  message=message, on_failing_function=self.append_message_to_queue)
            elif not test_connection:
                time.sleep(10)

            time.sleep(1)

        except Exception:
            self.logger.error(traceback.format_exc())

        finally:

            try:

                del queue

            except Exception:

                self.logger.error(traceback.format_exc())

    def append_message_to_queue(self, message, *args, **kwargs):

        try:

            self.offline_mode = True

            queue = persistqueue.SQLiteQueue(path=self.path_queue,
                                             name=self._related_edgebox_reference,
                                             auto_commit=True,
                                             multithreading=True)

            queue.put(message)

        except Exception:
            self.logger.error(traceback.format_exc())

        finally:

            try:

                del queue

            except Exception:

                self.logger.error(traceback.format_exc())

    def append_message_list_to_queue(self, message_list: list):
        try:

            for message in message_list:
                self.append_message_to_queue(message)

        except Exception:

            self.logger.error(traceback.format_exc())

    def kill(self):

        self.running = False
