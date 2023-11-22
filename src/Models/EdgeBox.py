import json
import threading
import time
import traceback
from src.DataClasses.FormatStatus import FormatUnplannedProduction
from src.Environnement.DashboardMonitoringVariableKeys import DashboardMonitoringVariableKeys
from src.Environnement.OfStatus import OfStatus
from src.Environnement.PanelVariableKeys import PanelVariableKeys
from src.Environnement.RedisTopicsEnum import RedisTopicsEnum
from src.Environnement.VariablesControl import VariablesControl
from src.Handlers.RedisPublishFromOfflineQueueHandler import RedisPublishFromOfflineQueueHandler
from src.Handlers.RevPiIoHandler import RevPiIoHandler
from src.InputOutput.OpcUaClient import OpcUaClient
from src.InputOutput.TypeIoConfig import TypeIoConfig
from src.Models.Machine import Machine
from src.Handlers.RedisPublishToPreProcessingHandler import RedisPublishToPreProcessingHandler
from src.Handlers.RestApiHandler import RestApiHandler
from src.Handlers.RedisHandler import RedisHandler
from src.Models.Line import Line
from src.Models.OF import OF


class EdgeBox:
    """""
        class variable list to save created edgebox
    """
    EDGE_BOX_SAVING_LIST = []

    def __init__(self, parent_class, io_config: json, edge_box_reference, edge_box_id):

        self.__parent_class = parent_class
        self.__is_of_enabled = self.__parent_class.get_is_of_enabled()
        self.__is_simulation_enabled = self.__parent_class.get_is_simulation_enabled()
        self.logger = self.__parent_class.logger

        self.__edge_box_id = edge_box_id
        self.__edge_box_reference = edge_box_reference

        self.__machines_affected_to_edge_box_list = []

        """ json edge box data like related machine and affected pins"""
        self.__config_json = io_config

        self.__redis_host = self.__parent_class.get_redis_host()
        self.__redis_port = self.__parent_class.get_redis_port()
        self.__redis_db = self.__parent_class.get_redis_db()
        self.__redis_password = self.__parent_class.get_redis_password()

        self.__port = self.__parent_class.get_port()
        self.__host = self.__parent_class.get_host()

        self.__redis_publisher_to_preprocessing = None
        self.__redis_publisher_from_offline_queue = None
        self.__input_output_setup = None

        self.__unplanned_production = False
        self.__unplanned_production_timer = 0

        self.__micro_stop_threshold = VariablesControl.micro_stop_threshold.value

        self.__incident_popup_shown = False

        self.__mold_state = 0

        self.io_handler = None

        self.__running = False

    """
     start edgebox process
    """

    def start_edge_box(self):
        try:
            self.__running = True

            is_edgebox_saved = self.save_edgebox(self)

            self.create_machines()

            if is_edgebox_saved:

                self.__redis_publisher_from_offline_queue = RedisPublishFromOfflineQueueHandler(related_edgebox=self)
                self.__redis_publisher_to_preprocessing = RedisPublishToPreProcessingHandler(related_edgebox=self)

                self.__redis_publisher_from_offline_queue.start()
                self.__redis_publisher_to_preprocessing.start()

                if self.__is_simulation_enabled:
                    self.io_handler = self.__parent_class.simulation_tool_manager
                else:
                    self.io_handler = RevPiIoHandler()

                self.__input_output_setup = TypeIoConfig(edge_box_reference=self.__edge_box_reference,
                                                         related_edge_box=self
                                                         )
                self.start_input_output_setup()

                if self.__is_of_enabled:

                    self.listen_to_postprocessing_shop_floor_data()

                    self.start_of(host=self.__host, port=self.__port)

                    lines = Line.get_lines_by_related_edge_box_reference(
                        related_edge_box_reference=self.__edge_box_reference)

                    for line in lines:
                        self.send_end_unplanned_production(line_id=line.get_line_id(), line_label=line.get_line_label())

        except Exception:
            self.logger.error(traceback.format_exc())

    """
    save edge box instance to edgebox saving list (class variable)
    """

    def save_edgebox(self, edge_box):
        try:

            if not any(edge.get_edge_box_reference() == edge_box.get_edge_box_reference()
                       for edge in EdgeBox.EDGE_BOX_SAVING_LIST):
                EdgeBox.EDGE_BOX_SAVING_LIST.append(edge_box)

                return True

            else:
                return False

        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    """""
    create machines from json    
    """

    def create_machines(self):
        try:

            for data in self.__config_json:

                if not Machine.check_if_machine_exist(machine_id=data[PanelVariableKeys.machine_id.value]) or \
                        data[PanelVariableKeys.machine_id.value] is None:

                    if data[PanelVariableKeys.machine_id.value] is not None:

                        machine = Machine(machine_reference=data[PanelVariableKeys.machine_reference.value],
                                          machine_id=data[PanelVariableKeys.machine_id.value],
                                          creator_edge_box=self)
                        is_machine_saved = machine.save_machine(machine)

                        if is_machine_saved:
                            machine.start_machine_process()

                            if data[PanelVariableKeys.panel_reference.value] == self.__edge_box_reference:

                                if not machine.check_if_edge_box_already_affected_to_the_machine \
                                            (edge_box_reference=self.__edge_box_reference):
                                    machine.get_related_edge_boxes_list().append(self)

                    else:

                        machine = Machine(machine_reference=None,
                                          machine_id=None,
                                          creator_edge_box=self)

                        is_machine_saved = machine.save_machine(machine)
                        if is_machine_saved:
                            machine.start_machine_process()

                    if data[PanelVariableKeys.panel_reference.value] == self.__edge_box_reference:
                        self.affect_machine_to_edge_box(new_machine=machine)

                        if not machine.check_if_edge_box_already_affected_to_the_machine \
                                    (edge_box_reference=self.__edge_box_reference):
                            machine.get_related_edge_boxes_list().append(self)

                else:
                    machine = Machine.get_machine_by_id(machine_id=data[PanelVariableKeys.machine_id.value])
                    if not machine.check_if_edge_box_already_affected_to_the_machine \
                                (edge_box_reference=self.__edge_box_reference):

                        machine.get_related_edge_boxes_list().append(self)
                        affected_pins = json.loads(data[PanelVariableKeys.affected_pins.value])

                        for pin in affected_pins:
                            machine.get_affected_pins().append(pin)

                        if data[PanelVariableKeys.panel_reference.value] == self.__edge_box_reference:
                            self.affect_machine_to_edge_box(new_machine=machine)

                        if str(data[PanelVariableKeys.post_id.value]) == str(machine.get_affected_post().get_post_id()):
                            machine.affect_opc_to_line(line_id=data[PanelVariableKeys.line_id.value],
                                                       edge_box_reference=data[PanelVariableKeys.panel_reference.value])

        except Exception:
            self.logger.error(traceback.format_exc())

    """"
     affect machines to edgebox list
     
     every edgebox have his own list of machines
     
     before affectation : verify if machine already affected to the edgebox affectation list                        
    """

    def affect_machine_to_edge_box(self, new_machine):
        try:

            if not any(
                    machine.get_machine_id() == new_machine.get_machine_id()
                    and machine.get_machine_reference() == new_machine.get_machine_reference()
                    for machine in self.__machines_affected_to_edge_box_list):
                self.__machines_affected_to_edge_box_list.append(new_machine)

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
    check of update from server (suspended , in progress, new of ...)
    """

    def listen_to_postprocessing_shop_floor_data(self):
        try:

            topic_consumer = RedisTopicsEnum.of_consumer_topic.value

            topic = topic_consumer.replace("{reference}", self.__edge_box_reference)

            redis = RedisHandler(redis_host=self.__redis_host,
                                 redis_port=self.__redis_port,
                                 redis_db=self.__redis_db,
                                 redis_password=self.__redis_password,
                                 parent_class=self
                                 )

            redis.redis_connect()

            redis.subscribe_to_specific_topic(topic)

            redis.bind_consumer_to_function(on_message_bind_function=self.update_of_on_redis_message)

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
    check existent of on server and create new instance for that of
    """

    def start_of(self, host, port):
        try:
            for line in Line.LINES_SAVING_LIST:

                json_conf = RestApiHandler().get_dashboard_by_line_id(host=host, port=port,
                                                                      line_id=line.get_line_id())

                if json_conf:

                    for config in json_conf:

                        if not OF.check_if_of_already_exist(config[DashboardMonitoringVariableKeys.of_id.value]):

                            of = OF(line_id=line.get_line_id(), line_label=line.get_line_label(),
                                    related_edgebox=self)

                            of.update_of_config(config)

                            is_of_saved = of.save_of(of)

                            if is_of_saved:

                                if line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                                            (edge_box_reference=self.__edge_box_reference):
                                    of.related_edge_boxes_list.append(self)

                                of.start_of_process(redis_host=self.__redis_host,
                                                    redis_port=self.__redis_port,
                                                    redis_password=self.__redis_password,
                                                    redis_db=self.__redis_db)
                        else:

                            of = OF.get_of_from_saving_list_by_dashboard_of_id(
                                dashboard_of_id=config[DashboardMonitoringVariableKeys.of_id.value])

                            if line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                                        (edge_box_reference=self.__edge_box_reference):
                                of.related_edge_boxes_list.append(self)

                                of.start_of_process(redis_host=self.__redis_host,
                                                    redis_port=self.__redis_port,
                                                    redis_password=self.__redis_password,
                                                    redis_db=self.__redis_db)

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
     get redis message
     
     if of exist update it with new information
     
     else create new of
    """

    def update_of_on_redis_message(self, message):
        try:
            msg = json.loads(message)
            of = OF.get_of_from_saving_list_by_dashboard_of_id(msg[DashboardMonitoringVariableKeys.of_id.value])

            if of is not None:

                of.update_of_config(msg)

            else:

                of = OF(line_id=msg[DashboardMonitoringVariableKeys.line_id.value],
                        line_label=msg['dashboardLineLabel'],
                        related_edgebox=self)

                of.update_of_config(msg)

                is_of_saved = of.save_of(of)
                if is_of_saved:

                    line = Line.get_line_by_id(line_id=msg[DashboardMonitoringVariableKeys.line_id.value])

                    if line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                                (edge_box_reference=self.__edge_box_reference):
                        of.related_edge_boxes_list.append(self)

                    of.start_of_process(redis_host=self.__redis_host,
                                        redis_port=self.__redis_port,
                                        redis_password=self.__redis_password,
                                        redis_db=self.__redis_db)

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_start_unplanned_production(self, line_id, line_label):
        try:
            self.__unplanned_production_timer = time.time()

            start_unplanned_stop = FormatUnplannedProduction(lineId=line_id
                                                             , lineLabel=line_label
                                                             , start=True
                                                             )

            start_unplanned_stop_msg = start_unplanned_stop.get_json_format()

            self.__redis_publisher_to_preprocessing.message_pile.append(str(start_unplanned_stop_msg))

            self.__unplanned_production = True
        except Exception:
            self.logger.error(traceback.format_exc())
            self.__unplanned_production = False

    def send_end_unplanned_production(self, line_id, line_label):
        try:
            end_unplanned_stop = FormatUnplannedProduction(lineId=line_id
                                                           , lineLabel=line_label
                                                           , start=False
                                                           )

            end_unplanned_stop_msg = end_unplanned_stop.get_json_format()

            self.__redis_publisher_to_preprocessing.message_pile.append(str(end_unplanned_stop_msg))

            self.__unplanned_production = False

        except Exception:
            self.logger.error(traceback.format_exc())
            self.__unplanned_production = True

    def detect_unplanned_production(self, line_id, line_label):
        try:
            of_list = OF.get_of_list_by_edge_box_reference(edge_box_reference=self.__edge_box_reference)

            active_of_list = list(
                filter(lambda _of: _of.get_of_status() == OfStatus.inprogress.value, of_list))

            if active_of_list:
                return

            elif self.__unplanned_production:
                """refresh started unplanned production timer on production detection"""
                self.__unplanned_production_timer = time.time()

            elif not self.__unplanned_production:
                """start unplanned production on first production detection"""
                self.send_start_unplanned_production(line_id=line_id, line_label=line_label)

                threading.Thread(target=self.calculate_idle_state,
                                 args=(line_id, line_label)).start()

        except Exception:
            self.logger.error(traceback.format_exc())

    def calculate_idle_state(self, line_id, line_label):
        try:

            while self.__running:

                of_list = OF.get_of_list_by_edge_box_reference(edge_box_reference=self.__edge_box_reference)

                active_of_list = list(
                    filter(lambda _of: _of.get_of_status() == OfStatus.inprogress.value, of_list))

                """wait for unplanned production end conditions"""
                if (
                        time.time() - self.__unplanned_production_timer >
                        VariablesControl.unplanned_production_threshold_value.value
                        and self.__unplanned_production

                ) or active_of_list:
                    self.send_end_unplanned_production(line_id=line_id, line_label=line_label)

                    return

                time.sleep(5)

        except Exception:
            self.logger.error(traceback.format_exc())

    def start_input_output_setup(self):
        try:
            for data in self.__config_json:

                if data[PanelVariableKeys.panel_reference.value] == self.__edge_box_reference:
                    affected_pins = json.loads(data[PanelVariableKeys.affected_pins.value]) if data else []

                    if affected_pins:

                        for pin in affected_pins:

                            if pin['typeCnx'] == 'TOR Entré' and str(pin['pin']).isnumeric():

                                rising_function, falling_function, changed_value = self.__input_output_setup. \
                                    get_callback_functions(
                                    pin_number=str(pin['pin']),
                                    type_io=str(pin['typeIo']),
                                    type_cnx=str(pin['typeCnx']),
                                    type_capteur=str(pin['typeCapteur'])
                                )

                                if type(rising_function) == list and type(falling_function) == list:

                                    for rising, falling in zip(rising_function, falling_function):
                                        self.io_handler.set_callback_function(pin=str(pin['pin']),
                                                                              rising_function=rising,
                                                                              falling_function=falling,
                                                                              type_capteur=str(pin['typeCapteur']),
                                                                              edge_box_reference=
                                                                              self.__edge_box_reference)
                                else:

                                    self.io_handler.set_callback_function(pin=str(pin['pin']),
                                                                          rising_function=rising_function,
                                                                          falling_function=falling_function,
                                                                          type_capteur=str(pin['typeCapteur']),
                                                                          edge_box_reference=
                                                                          self.__edge_box_reference)

                            elif pin['typeCnx'] == 'OPC' and str(pin['pin'].upper()) != "MANUEL":

                                opc_server_address = data[PanelVariableKeys.opc_server_adress.value]
                                if "opc.tcp://" not in opc_server_address and opc_server_address:
                                    opc_server_address = "opc.tcp://" + opc_server_address

                                if self.__is_simulation_enabled:
                                    port = opc_server_address.split(':')[-1]
                                    port = port.split('/')[0]
                                    opc_server_address = 'opc.tcp://127.0.0.1:{}/'.format(port)

                                    self.io_handler.opc_server_port = port
                                    self.io_handler.opc_variable_list.append(pin)
                                    self.io_handler.add_pin_config_to_home_page_table \
                                        (self.__edge_box_reference, str(pin['typeCapteur']), str(pin['pin']), "OPC")

                                opc_client = OpcUaClient(opc_url=opc_server_address, related_edge_box=self)

                                opc_client.start()

                                rising_function, falling_function, changed_value = self.__input_output_setup. \
                                    get_callback_functions(
                                    pin_number=str(pin['pin']),
                                    type_io=str(pin['typeIo']),
                                    type_cnx=str(pin['typeCnx']),
                                    type_capteur=str(pin['typeCapteur'])
                                )

                                opc_client.subscribe(node_id=str(pin['pin']), rising_function=rising_function,
                                                     falling_function=falling_function, changed_value=changed_value)

                            elif pin['typeCnx'] == 'TOR Sortie' and str(pin['pin']).isnumeric():

                                if self.__is_simulation_enabled:
                                    self.io_handler.enable_configured_output(pin=str(pin['pin']),
                                                                             type_capteur=str(
                                                                                 pin['typeCapteur'])
                                                                             )
        except Exception:
            self.logger.error(traceback.format_exc())

    def kill(self):
        self.__running = False

    """"
    getters and setters bloc
    """

    def get_edgebox_id(self):
        return self.__edge_box_id

    def set_edgebox_id(self, edgebox_id):
        self.__edge_box_id = edgebox_id

    def get_edge_box_reference(self):
        return self.__edge_box_reference

    def set_edge_box_reference(self, edge_box_reference):
        self.__edge_box_reference = edge_box_reference

    def get_machines_affected_to_edge_box_list(self):
        return self.__machines_affected_to_edge_box_list

    def set_machines_affected_to_edge_box_list(self, machines_affected_to_edge_box):
        self.__machines_affected_to_edge_box_list = machines_affected_to_edge_box

    def get_config_json(self):
        return self.__config_json

    def set_config_json(self, config_json):
        self.__config_json = config_json

    def get_is_of_enabled(self):
        return self.__is_of_enabled

    def set_is_of_enabled(self, use_of):
        self.__is_of_enabled = use_of

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

    def get_port(self):
        return self.__port

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def set_host(self, host):
        self.__host = host

    def get_redis_publisher_to_preprocessing(self):
        return self.__redis_publisher_to_preprocessing

    def set_redis_publisher_to_preprocessing(self, redis_publisher_to_preprocessing):
        self.__redis_publisher_to_preprocessing = redis_publisher_to_preprocessing

    def get_redis_publisher_from_offline_queue(self):
        return self.__redis_publisher_from_offline_queue

    def set_redis_publisher_from_offline_queue(self, redis_publisher_from_offline_queue):
        self.__redis_publisher_from_offline_queue = redis_publisher_from_offline_queue

    def get_input_output_setup(self):
        return self.__input_output_setup

    def set_input_output_setup(self, input_output_setup):
        self.__input_output_setup = input_output_setup

    def get_micro_stop_threshold(self):
        return self.__micro_stop_threshold

    def set_micro_stop_threshold(self, micro_stop_threshold):
        self.__micro_stop_threshold = micro_stop_threshold

    def get_incident_popup_shown(self):
        return self.__incident_popup_shown

    def set_incident_popup_shown(self, incident_popup_shown):
        self.__incident_popup_shown = incident_popup_shown

    def get_mold_state(self):
        return self.__mold_state

    def set_mold_state(self, mold_state):
        self.__mold_state = mold_state

    """"
    end of getters and setters bloc
    """
