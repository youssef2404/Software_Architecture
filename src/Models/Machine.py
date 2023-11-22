import json
import traceback

from src.Environnement.PanelVariableKeys import PanelVariableKeys
from src.Models.Line import Line
from src.Models.Post import Post


class Machine:
    """""
               class variable list to save created machines
    """
    MACHINES_SAVING_LIST = []

    def __init__(self, machine_reference, machine_id, creator_edge_box):

        self.__creator_edge_box = creator_edge_box
        self.__creator_edge_box_reference = self.__creator_edge_box.get_edge_box_reference()

        self.__port = self.__creator_edge_box.get_port()
        self.__host = self.__creator_edge_box.get_host()

        self.__config_json = self.__creator_edge_box.get_config_json()

        self.logger = self.__creator_edge_box.logger

        self.__machine_reference = machine_reference
        self.__machine_id = machine_id

        self.related_edge_boxes_list = []

        self.__affected_pins_list = []

        self.__affected_post_id = None
        self.__affected_post = None
        self.__affected_line = None

    @staticmethod
    def get_machine_with_edge_reference_and_affected_pin(related_edge_box_reference, pin_number, type_cnx,
                                                         type_capteur, type_io):
        return next((machine for machine in Machine.MACHINES_SAVING_LIST
                     if any(edge.get_edge_box_reference() == related_edge_box_reference
                            and machine.check_if_machine_matches(machine=machine, pin=pin_number,
                                                                 type_cnx=type_cnx, type_capteur=type_capteur,
                                                                 type_io=type_io)
                            for edge in machine.get_related_edge_boxes_list())), None)

    @staticmethod
    def check_if_machine_exist(machine_id):
        if machine_id is None:
            return False
        else:
            return any(machine.get_machine_id() == machine_id for machine in Machine.MACHINES_SAVING_LIST)

    @staticmethod
    def get_machine_by_id(machine_id):
        return next((machine for machine in Machine.MACHINES_SAVING_LIST
                     if str(machine.get_machine_id()) == str(machine_id)), None)

    def check_if_edge_box_already_affected_to_the_machine(self, edge_box_reference):
        return any(edge_box.get_edge_box_reference() == edge_box_reference for edge_box in self.related_edge_boxes_list)

    def start_machine_process(self):
        try:
            self.create_posts()

            self.affect_machine_to_post()

            self.start_pins_affectation()

            self.get_related_line()

        except Exception:
            self.logger.error(traceback.format_exc())

    def check_if_machine_matches(self, machine, pin, type_cnx, type_capteur, type_io):
        try:

            found = any(str(affected_pin['pin']) == str(pin) and affected_pin['typeCnx'] == type_cnx \
                        and affected_pin['typeCapteur'] == type_capteur and str(affected_pin['typeIo']) == str(type_io)
                        for affected_pin in machine.get_affected_pins())

            return found

        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    def create_posts(self):
        try:
            for data in self.__config_json:

                if data[PanelVariableKeys.post_id.value] is not None:

                    self.__affected_post_id = data[PanelVariableKeys.post_id.value]

                    if not Post.check_if_post_exist(post_id=data[PanelVariableKeys.post_id.value]):
                        post = Post(post_reference=data[PanelVariableKeys.post_reference.value],
                                    post_id=data[PanelVariableKeys.post_id.value],
                                    creator_machine=self
                                    )

                        is_post_saved = post.save_post(post=post)

                        if is_post_saved:
                            self.__affected_post = post
                            post.start_post_process()
                    else:
                        post = Post.get_post_by_id(post_id=self.__affected_post_id)
                        self.__affected_post = post

                        if str(post.get_affected_line_id()) == str(data[PanelVariableKeys.line_id.value]):
                            post.affect_edge_box_to_line(edge_box_reference=
                                                         data[PanelVariableKeys.panel_reference.value])
        except Exception:
            self.logger.error(traceback.format_exc())

    def affect_machine_to_post(self):
        try:
            for post in Post.POSTS_SAVING_LIST:
                if self.__affected_post_id == post.get_post_id():
                    post.get_post_machines_list().append(self)

        except Exception:
            self.logger.error(traceback.format_exc())

    """""
                 verify if machine exist in the saving list (machine list)
                 if not save it
    """

    def save_machine(self, machine):
        try:

            if not any(machine_.__machine_id == machine.__machine_id
                       and machine_.get_creator_edge_box_reference() == machine.get_creator_edge_box_reference()
                       for machine_ in Machine.MACHINES_SAVING_LIST):
                Machine.MACHINES_SAVING_LIST.append(machine)
                return True

            else:
                return False

        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    def get_related_line(self):
        try:
            if not self.__affected_line:
                self.__affected_line = Line.get_line_by_id(line_id=self.__affected_post.get_affected_line_id())
        except Exception:
            self.logger.error(traceback.format_exc())
            self.__affected_line = None

    """"" 
    read affected pins 
    """

    def start_pins_affectation(self):
        try:

            pins_data = next((data for data in self.__config_json
                              if str(data[PanelVariableKeys.machine_id.value]) == str(self.__machine_id)), None)

            self.__affected_pins_list = json.loads(
                pins_data[PanelVariableKeys.affected_pins.value]) if pins_data else []

        except Exception:
            self.logger.error(traceback.format_exc())

    def affect_opc_to_line(self, line_id, edge_box_reference):
        if str(line_id) == str(self.get_affected_post().get_affected_line_id()):
            if not self.get_affected_post().get_affected_line(). \
                    check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                        (edge_box_reference=edge_box_reference):
                self.get_affected_post().get_affected_line().get_related_edge_boxes_reference_list(). \
                    append(edge_box_reference)

    """"
       getters and setters bloc
    """

    def get_affected_pins(self):
        return self.__affected_pins_list

    def set_affected_pins(self, affected_pins):
        self.__affected_pins_list = affected_pins

    def get_affected_post_id(self):
        return self.__affected_post_id

    def set_affected_post_id(self, affected_post):
        self.__affected_post_id = affected_post

    def get_machine_reference(self):
        return self.__machine_reference

    def set_machine_reference(self, machine_reference):
        self.__machine_reference = machine_reference

    def get_creator_edge_box_reference(self):
        return self.__creator_edge_box_reference

    def set_creator_edge_box_reference(self, creator_edge_box_reference):
        self.__creator_edge_box_reference = creator_edge_box_reference

    def get_machine_id(self):
        return self.__machine_id

    def set_machine_id(self, machine_id):
        self.__machine_id = machine_id

    def get_config_json(self):
        return self.__config_json

    def set_config_json(self, config_json):
        self.__config_json = config_json

    def get_related_edge_boxes_list(self):
        return self.related_edge_boxes_list

    def set_related_edge_boxes_list(self, related_edge_boxes_list):
        self.related_edge_boxes_list = related_edge_boxes_list

    def get_port(self):
        return self.__port

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def set_host(self, host):
        self.__host = host

    def get_affected_post(self):
        return self.__affected_post

    def set_affected_post(self, affected_post):
        self.__affected_post = affected_post

    def get_affected_line(self):
        return self.__affected_line

    def set_affected_line(self, affected_line):
        self.__affected_line = affected_line

    """"
    end of getters and setters bloc
    """
