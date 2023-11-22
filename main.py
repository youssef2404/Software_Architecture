import threading
import traceback

from src.Environnement.ConfigurationFileVariableKeys import ConfigurationFileVariableKeys
from src.Environnement.PanelVariableKeys import PanelVariableKeys
from src.Handlers.RestApiHandler import RestApiHandler
from src.Handlers.InternalResourceHandler import InternalResourceHandler
from src.Models.EdgeBox import EdgeBox
from src.Utilities.Logger import Logger


class Main:

    def __init__(self):
        self.__port = None
        self.__host = None

        self.__references_list = []

        self.__redis_host = None
        self.__redis_port = None
        self.__redis_db = None
        self.__redis_password = None

        self.__is_of_enabled = None

        self.__is_simulation_enabled = False
        self.simulation_tool_manager = None
        self.wait_for_edge_box_config = threading.Event()

        self.logger = Logger(log_file_name="main-SF-Log.log",
                             log_file_directory="log-files")

    def run(self):
        try:
            self.read_config_file_data()

            if self.__is_simulation_enabled:
                from src.Simulation.SimulationToolManager import SimulationToolManager
                self.simulation_tool_manager = SimulationToolManager(parent_class=self)
                self.simulation_tool_manager.start()
                self.simulation_tool_manager.set_up_ui_completed.wait()

            for reference in self.__references_list:

                loaded_data = RestApiHandler.get_panel_by_reference(host=self.__host, port=self.__port,
                                                                    reference=reference)

                """""
                verify if edge box have data in the server after that create a new edge box
                if edgebox reference is not None and edge box is not already saved in the saving list
                """

                if loaded_data is not None:
                    edge_box_list = \
                        [EdgeBox(parent_class=self, io_config=loaded_data,
                                 edge_box_reference=data[PanelVariableKeys.panel_reference.value]
                                 , edge_box_id=data[PanelVariableKeys.panel_id.value])
                         for data in loaded_data
                         if data[PanelVariableKeys.panel_reference.value] is not None
                         and not self.check_if_edge_box_reference_already_exists(
                            edge_box_reference=data[PanelVariableKeys.panel_reference.value])
                         ]

                    list(map(lambda edge_box: edge_box.start_edge_box(), edge_box_list))

            if self.__is_simulation_enabled:
                self.wait_for_edge_box_config.set()

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
    get api io_config from io_config file
    """

    def get_url_and_references_list_from_config_file(self, configuration):
        try:

            if configuration is not None:

                for panel in configuration:
                    self.__host = panel[ConfigurationFileVariableKeys.host.value]
                    self.__port = panel[ConfigurationFileVariableKeys.post_processing_port.value]
                    self.__references_list = panel[ConfigurationFileVariableKeys.references_list.value]

                return configuration

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
    get redis io_config from io_config file
    """

    def load_redis_config_from_config_file(self, configuration):
        try:

            if configuration is not None:

                for panel in configuration:

                    self.__redis_host = str(panel[ConfigurationFileVariableKeys.redis_host.value]). \
                        replace("{host}", panel[ConfigurationFileVariableKeys.host.value])

                    if not self.__redis_host:
                        self.__redis_host = panel[ConfigurationFileVariableKeys.host.value]

                    self.__redis_port = panel[ConfigurationFileVariableKeys.redis_port.value]
                    self.__redis_db = panel[ConfigurationFileVariableKeys.redis_db.value]
                    self.__redis_password = panel[ConfigurationFileVariableKeys.redis_password.value] if \
                        panel[ConfigurationFileVariableKeys.redis_password.value] else None

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
    check if the project is with of or not
    if self.__is_of_enabled == ok 
    the project contains of 
    """

    def check_is_of_and_simulation_enabled(self, configuration):

        try:

            if configuration is not None:

                for panel in configuration:
                    self.__is_of_enabled = eval(str(panel[ConfigurationFileVariableKeys.check_if_of_enabled.value])
                                                .capitalize())

                    self.__is_simulation_enabled = eval(str(
                        panel[ConfigurationFileVariableKeys.check_if_simulation_enabled.value]).capitalize())

        except Exception:
            self.logger.error(traceback.format_exc())

    def setup_logger_information_from_configuration_file(self, configuration):
        try:
            is_printing = False
            log_level = "ERROR"

            if configuration is not None:

                for panel in configuration:
                    is_printing = panel[ConfigurationFileVariableKeys.console_log.value]
                    log_level = panel[ConfigurationFileVariableKeys.log_level.value]

            self.logger.setup_logger_information(log_file_name="main-SF-Log.log",
                                                 log_file_directory="log-files",
                                                 is_printing=is_printing,
                                                 log_level=log_level)

            self.logger.configure_logging_setup()

        except Exception:
            self.logger.error(traceback.format_exc())

    def read_config_file_data(self):

        try:
            """"
             get edge box references list
             get host 
             get port
             from local configfile.json
             and return io_config (type dict) with the io_config from configuration file to avoid reopening configfile.json             
            """

            config = InternalResourceHandler.load_config_from_config_file(
                config_file_path="ConfigurationFile.json",
                function=self.get_url_and_references_list_from_config_file)

            """ 
            load redis io_config from io_config variable 
            redis port , redis password ...
            """

            InternalResourceHandler. \
                load_config_from_config_file(config_file_path="",
                                             function=
                                             self.load_redis_config_from_config_file,
                                             config=config)

            """"
             load Is_OF_enabled bool variable from io_config variable to check if the architecture have of or not
            """

            InternalResourceHandler.load_config_from_config_file(config_file_path="",
                                                                 function=
                                                                 self.check_is_of_and_simulation_enabled,
                                                                 config=config)
            """
            load is printing and log level from config file 
            """

            InternalResourceHandler.load_config_from_config_file(config_file_path="",
                                                                 function=
                                                                 self.setup_logger_information_from_configuration_file,
                                                                 config=config)

        except Exception:
            self.logger.error(traceback.format_exc())

    """
    check if edge box already saved 
    if edgebox exist return true
    else return false
    """

    def check_if_edge_box_reference_already_exists(self, edge_box_reference):
        try:
            return any(
                edge_box.get_edge_box_reference() == edge_box_reference for edge_box in EdgeBox.EDGE_BOX_SAVING_LIST)
        except:
            self.logger.error(traceback.format_exc())
            return False

    """"
    getters and setters bloc
    """

    def get_port(self):
        return self.__port

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def set_host(self, host):
        self.__host = host

    def get_references_list(self):
        return self.__references_list

    def set_references_list(self, references_list):
        self.__references_list = references_list

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

    def get_is_of_enabled(self):
        return self.__is_of_enabled

    def set_is_of_enabled(self, use_of):
        self.__is_of_enabled = use_of

    def get_is_simulation_enabled(self):
        return self.__is_simulation_enabled

    def set_is_simulation_enabled(self, is_simulation_enabled):
        self.__is_simulation_enabled = is_simulation_enabled

    """"
    end of getters and setters bloc
    """


if __name__ == '__main__':
    main = Main()
    main.run()
