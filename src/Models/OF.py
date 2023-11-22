import json
import traceback

from src.Environnement.DashboardMonitoringVariableKeys import DashboardMonitoringVariableKeys
from src.Environnement.OfModes import OfModes
from src.Environnement.OfStatus import OfStatus
from src.Environnement.OfType import OfType
from src.Environnement.RedisTopicsEnum import RedisTopicsEnum
from src.Handlers.RedisHandler import RedisHandler
from src.Handlers.RestApiHandler import RestApiHandler


class OF:
    of_saving_list = []

    def __init__(self, line_id, line_label, related_edgebox):
        self.__creator_edgebox = related_edgebox

        self.logger = self.__creator_edgebox.logger

        self.__dashboard_of_id = None

        self.__of_status = None
        self.__of_type = None
        self.__of_mode = None

        self.__of_quantity_by_mold = None
        self.__of_product_theoretical_cycle = None
        self.__of_theoretical_cycle = None
        self.__of_theoretical_cycle_CC = None

        self.__creation_tag = None
        self.__mode_qualification = False
        self.__stop_cause_specified = True

        self.__of_line_label = line_label
        self.__of_line_id = line_id

        self.__workshop_id = None
        self.__workshop_label = None

        self.__mold_label = ""
        self.__mold_id = ""

        self.micro_stop_cause = "Micro Arret"
        self.micro_stop_category = "Micro Arret"

        self.up_down_time_consumer_topic = None
        self.redisHandler = None

        self.related_edge_boxes_list = []

        self.io_setup = self.__creator_edgebox.get_input_output_setup()

        self.port = self.__creator_edgebox.get_port()
        self.host = self.__creator_edgebox.get_host()

        self.end_stop_not_sent = self.io_setup.sender.end_stop_not_sent
        self.begin_stop_not_sent = self.io_setup.sender.begin_stop_not_sent
        self.start_stop_timer = self.io_setup.sender.start_stop_timer
        self.incident_message_not_sent = self.io_setup.sender.incident_message_not_sent

    @staticmethod
    def check_if_of_already_exist(dashboard_of_id):
        return any(of.get_dashboard_of_id() == dashboard_of_id for of in OF.of_saving_list)

    @staticmethod
    def get_of_from_saving_list_by_dashboard_of_id(dashboard_of_id):

        matching_of_list = [of for of in OF.of_saving_list if of.get_dashboard_of_id() == dashboard_of_id]

        if matching_of_list:
            return matching_of_list[0]  # get the first detected of that dashboard_of_id matches

    @staticmethod
    def get_of_list_by_edge_box_reference(edge_box_reference):
        of_list = []
        for of in OF.of_saving_list:
            for edge in of.related_edge_boxes_list:
                if edge.get_edge_box_reference() == edge_box_reference:
                    of_list.append(of)
        return of_list

    def start_of_process(self, redis_host, redis_port, redis_password, redis_db):
        try:
            of_list = [self]
            self.io_setup.sender.send_stop_start(line_id=self.__of_line_id, line_label=self.__of_line_label,
                                                 of_list=of_list,
                                                 is_machine_physically_in_stop=
                                                 self.io_setup.is_machine_physically_in_stop(),
                                                 is_of_enabled=True
                                                 )

            self.listen_to_up_down_time_consumer_topic(redis_host=redis_host,
                                                       redis_port=redis_port,
                                                       redis_password=redis_password,
                                                       redis_db=redis_db)
        except Exception:
            self.logger.error(traceback.format_exc())

    """
    update of configuration after redis message
    """

    def update_of_config(self, of_config):
        try:

            if self.__of_line_id == of_config[DashboardMonitoringVariableKeys.line_id.value] and \
                    of_config[DashboardMonitoringVariableKeys.of_status.value] != OfStatus.closed.value:

                self.__of_status = of_config[DashboardMonitoringVariableKeys.of_status.value]
                self.__dashboard_of_id = of_config[DashboardMonitoringVariableKeys.of_id.value]

                self.__of_type = of_config[DashboardMonitoringVariableKeys.of_type.value]
                self.__of_mode = of_config[DashboardMonitoringVariableKeys.of_mode.value]

                self.__of_quantity_by_mold = of_config[DashboardMonitoringVariableKeys.of_quantity_by_mold.value]
                self.__of_product_theoretical_cycle = float(
                    of_config[DashboardMonitoringVariableKeys.of_product_theoretical_cycle.value] / 1000)

                self.__of_theoretical_cycle_CC = float(
                    of_config[DashboardMonitoringVariableKeys.of_theoretical_cycle_cc.value] / 1000)

                self.__creation_tag = of_config[DashboardMonitoringVariableKeys.of_creation_tag.value]

                self.__workshop_id = of_config[DashboardMonitoringVariableKeys.workshop_id.value]
                self.__workshop_label = of_config[DashboardMonitoringVariableKeys.workshop_label.value]

                if self.__of_product_theoretical_cycle is not None:

                    if self.__of_quantity_by_mold is None:
                        self.__of_quantity_by_mold = 0

                    self.__of_theoretical_cycle = self.__of_product_theoretical_cycle * self.__of_quantity_by_mold
                self.get_of_mold_using_of_api()

            elif of_config[DashboardMonitoringVariableKeys.of_status.value] == OfStatus.closed.value:
                self.close_of(self)

        except Exception:
            self.logger.error(traceback.format_exc())

    def get_of_mold_using_of_api(self):
        try:
            of_data = RestApiHandler.get_of_by_of_id(host=self.host,
                                                     port=self.port,
                                                     of_reference=self.__dashboard_of_id)

            if of_data is not None:

                for of in of_data:
                    self.__mold_label = of[DashboardMonitoringVariableKeys.mold_label.value]
                    self.__mold_id = of[DashboardMonitoringVariableKeys.mold_id.value]

        except Exception:
            self.logger.error(traceback.format_exc())

    def save_of(self, of):
        try:

            if not any(_of.get_dashboard_of_id() == of.get_dashboard_of_id() for _of in OF.of_saving_list) \
                    and of.get_of_status() is not None and of.get_of_type() != OfType.waiting.value \
                    and of.get_of_mode() == OfModes.Auto.value:
                OF.of_saving_list.append(of)

                return True

            return False
        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    def listen_to_up_down_time_consumer_topic(self, redis_host, redis_port, redis_password, redis_db):

        self.up_down_time_consumer_topic = RedisTopicsEnum.up_down_time_consumer_topic.value. \
            replace("{reference}", self.__creator_edgebox.get_edge_box_reference())

        self.redisHandler = RedisHandler(redis_host=redis_host,
                                         redis_port=redis_port,
                                         redis_password=redis_password,
                                         redis_db=redis_db,
                                         parent_class=self)

        self.redisHandler.redis_connect()

        self.redisHandler.subscribe_to_specific_topic(self.up_down_time_consumer_topic)

        self.redisHandler.bind_consumer_to_function(
            on_message_bind_function=self.detect_manual_stop
        )

    def detect_manual_stop(self, message):

        try:
            manual_stop_message = json.loads(message)

            if manual_stop_message["ofId"] == self.__dashboard_of_id \
                    and manual_stop_message["lineId"] == self.__of_line_id:

                self.logger.info("received stop message from post processing: {}".format(manual_stop_message))

                if (self.__of_type == OfType.production.value
                    and self.__of_status == OfStatus.inprogress.value) \
                        or (self.__of_type == OfType.cc.value
                            and self.__of_status == OfStatus.inprogress.value):

                    if manual_stop_message["data"] == "start":

                        self.__mode_qualification = True

                        self.end_stop_not_sent = True
                        self.begin_stop_not_sent = False
                        self.start_stop_timer = 0

                    elif manual_stop_message["data"] == "finish":

                        self.__stop_cause_specified = True

                        self.__creator_edgebox.set_incident_popup_shown(incident_popup_shown=False)

                        self.end_stop_not_sent = False
                        self.begin_stop_not_sent = True
                        self.incident_message_not_sent = False

                        self.__mode_qualification = False

        except Exception:
            self.logger.error(traceback.format_exc())

    """"
     close of after redis message
    """

    def close_of(self, of):
        try:

            OF.of_saving_list.remove(of)

        except Exception:
            self.logger.error(traceback.format_exc())

    """"
    getters and setters bloc
    """

    def get_dashboard_of_id(self):
        return self.__dashboard_of_id

    def set_dashboard_of_id(self, of_id):
        self.__dashboard_of_id = of_id

    def get_of_status(self):
        return self.__of_status

    def set_of_status(self, of_status):
        self.__of_status = of_status

    def get_of_type(self):
        return self.__of_type

    def set_of_type(self, of_type):
        self.__of_type = of_type

    def get_of_mode(self):
        return self.__of_mode

    def set_of_mode(self, of_mode):
        self.__of_mode = of_mode

    def get_of_quantity_by_mold(self):
        return self.__of_quantity_by_mold

    def set_of_quantity_by_mold(self, of_quantity_by_mold):
        self.__of_quantity_by_mold = of_quantity_by_mold

    def get_of_product_theoretical_cycle(self):
        return self.__of_product_theoretical_cycle

    def set_of_product_theoretical_cycle(self, of_product_theoretical_cycle):
        self.__of_product_theoretical_cycle = of_product_theoretical_cycle

    def get_of_theoretical_cycle(self):
        return self.__of_theoretical_cycle

    def set_of_theoretical_cycle(self, of_theoretical_cycle):
        self.__of_theoretical_cycle = of_theoretical_cycle

    def get_of_theoretical_cycle_cc(self):
        return self.__of_theoretical_cycle_CC

    def set_of_theoretical_cycle_cc(self, of_theoretical_cycle_cc):
        self.__of_theoretical_cycle_CC = of_theoretical_cycle_cc

    def get_of_creation_tag(self):
        return self.__creation_tag

    def set_of_creation_tag(self, of_creation_tag):
        self.__creation_tag = of_creation_tag

    def get_of_line_id(self):
        return self.__of_line_id

    def set_of_line_id(self, of_line_id):
        self.__of_line_id = of_line_id

    def get_of_line_label(self):
        return self.__of_line_label

    def set_of_line_label(self, of_line_label):
        self.__of_line_label = of_line_label

    def get_of_workshop_id(self):
        return self.__workshop_id

    def set_of_workshop_id(self, workshop_id):
        self.__workshop_id = workshop_id

    def get_of_workshop_label(self):
        return self.__workshop_label

    def set_of_workshop_label(self, workshop_label):
        self.__workshop_label = workshop_label

    def get_of_mold_id(self):
        return self.__mold_id

    def set_of_mold_id(self, mold_id):
        self.__mold_id = mold_id

    def get_of_mold_label(self):
        return self.__mold_label

    def set_of_mold_label(self, mold_label):
        self.__mold_label = mold_label

    def get_of_creator_edgebox(self):
        return self.__creator_edgebox

    def set_of_creator_edgebox(self, related_edgebox):
        self.__creator_edgebox = related_edgebox

    def get_mode_qualification(self):
        return self.__mode_qualification

    def set_mode_qualification(self, mode_qualification):
        self.__mode_qualification = mode_qualification

    def get_stop_cause_specified(self):
        return self.__stop_cause_specified

    def set_stop_cause_specified(self, stop_cause_specified):
        self.__stop_cause_specified = stop_cause_specified

    """"
    end of getters and setters bloc
    """
