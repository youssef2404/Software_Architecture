import traceback

from src.Environnement.PanelVariableKeys import PanelVariableKeys
from src.Models.Line import Line


class Post:
    """""
            class variable list to save created posts
    """
    POSTS_SAVING_LIST = []

    def __init__(self, post_reference: str, post_id: int, creator_machine):

        self.__creator_machine = creator_machine

        self.__config_json = self.__creator_machine.get_config_json()

        self.logger = self.__creator_machine.logger

        self.__post_reference = post_reference
        self.__post_id = post_id

        self.__post_machines_list = []

        self.__port = self.__creator_machine.get_port()
        self.__host = self.__creator_machine.get_host()

        self.__affected_line_id = None
        self.__affected_line = None

    @staticmethod
    def check_if_post_exist(post_id):
        return any(str(post.get_post_id()) == str(post_id) for post in Post.POSTS_SAVING_LIST)

    @staticmethod
    def get_post_by_id(post_id):

        return next((post for post in Post.POSTS_SAVING_LIST if str(post.get_post_id()) == str(post_id)), None)

    """
    the post process is : -create line from json conf (from server) if it doesnt exist

                          -affect line to post if post is not related to any line 
    """

    def start_post_process(self):
        try:
            self.create_lines()
            self.affect_post_to_line()
        except Exception:
            self.logger.error(traceback.format_exc())

    """""
              verify if post exist in the saving list (post list)
              if not save it
    """

    def save_post(self, post):
        try:
            if not any(str(post_.get_post_id()) == str(post.get_post_id()) for post_ in Post.POSTS_SAVING_LIST):

                Post.POSTS_SAVING_LIST.append(post)

                return True
            else:
                return False

        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    """
      every post can have one or many machines

      this function is to add machines to the post machines list 

      affectation of machines to the related post
    """

    def add_machine_to_post_machines_list(self, new_machine):
        try:

            if not any(machine.get_machine_id() == new_machine.get_machine_id()
                       for machine in self.get_post_machines_list()):
                self.get_post_machines_list().append(new_machine)

        except Exception:
            self.logger.error(traceback.format_exc())

    """
     create a new line from json conf (from server) if it doesnt exist
    """

    def create_lines(self):
        for data in self.__config_json:

            if data[PanelVariableKeys.line_id.value] is not None:

                self.__affected_line_id = data[PanelVariableKeys.line_id.value]

                if not Line.check_if_line_exist(line_id=data[PanelVariableKeys.line_id.value]):

                    line = Line(line_id=data[PanelVariableKeys.line_id.value],
                                line_label=data[PanelVariableKeys.line_label.value],
                                creator_post=self
                                )

                    is_line_saved = line.save_line(line=line)
                    if is_line_saved:
                        self.__affected_line = line

                        if not line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                                    (edge_box_reference=data[PanelVariableKeys.panel_reference.value]):
                            line.get_related_edge_boxes_reference_list(). \
                                append(data[PanelVariableKeys.panel_reference.value])

                        line.start_line_process()
                else:
                    line = Line.get_line_by_id(line_id=self.__affected_line_id)

                    if not line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                                (edge_box_reference=data[PanelVariableKeys.panel_reference.value]):
                        line.get_related_edge_boxes_reference_list(). \
                            append(data[PanelVariableKeys.panel_reference.value])

                    self.__affected_line = line

    """
    every post is related to one line

    this function is to affect the post to a specific line
    """

    def affect_post_to_line(self):

        for line in Line.LINES_SAVING_LIST:

            if self.__affected_line_id == line.get_line_id():
                line.get_line_posts_list().append(self)

    def affect_edge_box_to_line(self, edge_box_reference):
        if not self.__affected_line.check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list \
                    (edge_box_reference=edge_box_reference):
            self.__affected_line.get_related_edge_boxes_reference_list().append(edge_box_reference)

    """"
    getters and setters bloc
    """

    def get_post_reference(self):
        return self.__post_reference

    def set_post_reference(self, post_reference):
        self.__post_reference = post_reference

    def get_post_id(self):
        return self.__post_id

    def set_post_id(self, post_id):
        self.__post_id = post_id

    def get_config_json(self):
        return self.__config_json

    def set_config_json(self, config_json):
        self.__config_json = config_json

    def get_post_machines_list(self):
        return self.__post_machines_list

    def set_post_machines_list(self, post_machines_list):
        self.__post_machines_list = post_machines_list

    def get_affected_line_id(self):
        return self.__affected_line_id

    def set_affected_line_id(self, affected_line_id):
        self.__affected_line_id = affected_line_id

    def get_affected_line(self):
        return self.__affected_line

    def set_affected_line(self, affected_line):
        self.__affected_line = affected_line

    def get_port(self):
        return self.__port

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def set_host(self, host):
        self.__host = host

    """"
    end of getters and setters bloc
    """
