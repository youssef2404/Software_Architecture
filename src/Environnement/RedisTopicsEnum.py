from enum import Enum


class RedisTopicsEnum(str, Enum):
    """ consumers"""
    up_down_time_consumer_topic = "{reference}->postprocessing->shopfloordata->up_down_time"
    of_consumer_topic = "{reference}->postprocessing->shopfloordata"
    edge_box_command = "{reference}->postprocessing->EdgeBox->command"
    topicConsumerControl = "{reference}->postprocessing->shopfloorcontrol",

    """ publishers"""
    production_topic = "shopfloordata->preprocessing"

    offline_queue_path = "offline_queues/smartfactory19-"
