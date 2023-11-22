import json
import threading
import traceback
from pathlib import Path

from src.Environnement.PanelVariableKeys import PanelVariableKeys
from src.Handlers.RestApiHandler import RestApiHandler
from src.Models.Workshop import Workshop
from src.Utilities.Logger import Logger


class Line:
    """""
        class variable list to save created lines
    """
    LINES_SAVING_LIST = []

    def __init__(self, line_id: int, line_label: str, creator_post):
        self.__creator_post = creator_post
        self.__config_json = self.__creator_post.get_config_json()

        self.__port = self.__creator_post.get_port()
        self.__host = self.__creator_post.get_host()

        self.__line_id = line_id
        self.__line_label = line_label
        self.__line_posts_list = []

        self.__affected_workshop_id = None
        self.__affected_workshop = None

        self.__related_edge_boxes_references_list = []

        self.logger = self.__creator_post.logger

    @staticmethod
    def get_lines_by_related_edge_box_reference(related_edge_box_reference):
        return [line for line in Line.LINES_SAVING_LIST if
                related_edge_box_reference in line.get_related_edge_boxes_reference_list()]

    @staticmethod
    def check_if_line_exist(line_id):
        return any(str(line.get_line_id()) == str(line_id) for line in Line.LINES_SAVING_LIST)

    @staticmethod
    def get_line_by_id(line_id):
        return next((line for line in Line.LINES_SAVING_LIST if str(line.get_line_id()) == str(line_id)), None)

    def check_if_edge_box_reference_is_affected_to_line_related_edge_boxes_references_list(self, edge_box_reference):
        if edge_box_reference in self.__related_edge_boxes_references_list:
            return True
        else:
            return False

    """
      the line process is : -create workshop from json conf (from server) if it doesnt exist

                          -affect workshop to line if line is not related to any workshop 
    """

    def start_line_process(self):
        try:
            self.create_workshop()

            self.affect_line_to_workshop()

        except Exception:
            self.logger.error(traceback.format_exc())

    """
    every line can have one or many posts 

    so this function is to affect the posts the their related line

    every line have a list of posts called line_posts_list
    """

    def add_posts_to_line_posts_list(self, new_post):
        try:
            if not any(post.get_post_id() == new_post.get_post_id()
                       for post in self.__line_posts_list):
                self.get_line_posts_list().append(new_post)
        except Exception:
            self.logger.error(traceback.format_exc())

    """""
           verify if line already exist
           if not save it
    """

    def save_line(self, line):
        try:
            if not any(str(line_.get_line_id()) == str(line.get_line_id()) for line_ in Line.LINES_SAVING_LIST):

                Line.LINES_SAVING_LIST.append(line)

                return True

            else:

                return False
        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    """     
     create a new workshop from json conf (from server) if it doesnt exist
    """

    def create_workshop(self):
        try:
            for data in self.__config_json:

                if data[PanelVariableKeys.workshop_id.value] is not None:

                    self.__affected_workshop_id = data[PanelVariableKeys.workshop_id.value]

                    if not Workshop.check_if_workshop_exist(workshop_id=data[PanelVariableKeys.workshop_id.value]):

                        workshop = Workshop(workshop_id=data[PanelVariableKeys.workshop_id.value],
                                            workshop_label=data[PanelVariableKeys.workshop_label.value]
                                            , creator_line=self)

                        is_workshop_saved = workshop.save_workshop(workshop=workshop)
                        if is_workshop_saved:
                            self.__affected_workshop = workshop
                    else:
                        workshop = Workshop.get_workshop_by_id(workshop_id=self.__affected_workshop_id)
                        self.__affected_workshop = workshop
                else:

                    """
                     in the opc data there is no workshop id so we consume get_line_by_line_id Rest Api

                     to get the line information and the related workshop to that line
                    """

                    line_data = RestApiHandler.get_line_by_line_id(host=self.__host,
                                                                   port=self.__port,
                                                                   line_id=self.__line_id)
                    if line_data:

                        if line_data['lineWorkshopId'] is not None:

                            self.__affected_workshop_id = line_data['lineWorkshopId']

                            if not Workshop.check_if_workshop_exist(workshop_id=line_data['lineWorkshopId']):

                                workshop = Workshop(workshop_id=line_data['lineWorkshopId'],
                                                    workshop_label=line_data['lineWorkShopLabel']
                                                    , creator_line=self)

                                is_workshop_saved = workshop.save_workshop(workshop=workshop)

                                if is_workshop_saved:
                                    self.__affected_workshop = workshop
                            else:
                                workshop = Workshop.get_workshop_by_id(workshop_id=self.__affected_workshop_id)
                                self.__affected_workshop = workshop

        except Exception:
            self.logger.error(traceback.format_exc())

    """    
    every line is related to one workshop

    this function is to affect the line to a specific workshop    
    """

    def affect_line_to_workshop(self):
        try:
            for workshop in Workshop.WORKSHOPS_SAVING_LIST:
                if self.__affected_workshop_id == workshop.get_workshop_id():
                    workshop.get_workshop_line_list().append(self)
        except Exception:
            self.logger.error(traceback.format_exc())

    """"
    getters and setters bloc
    """

    def get_line_id(self):
        return self.__line_id

    def set_line_id(self, line_id):
        self.__line_id = line_id

    def get_line_label(self):
        return self.__line_label

    def set_line_label(self, line_label):
        self.__line_label = line_label

    def get_config_json(self):
        return self.__config_json

    def set_config_json(self, config_json):
        self.__config_json = config_json

    def get_line_posts_list(self):
        return self.__line_posts_list

    def set_line_posts_list(self, line_posts_list):
        self.__line_posts_list = line_posts_list

    def get_affected_workshop_id(self):
        return self.__affected_workshop_id

    def set_affected_workshop_id(self, affected_workshop):
        self.__affected_workshop_id = affected_workshop

    def get_port(self):
        return self.__port

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def set_host(self, host):
        self.__host = host

    def get_related_edge_boxes_reference_list(self):
        return self.__related_edge_boxes_references_list

    def set_related_edge_boxes_reference_list(self, related_edge_boxes_references_list):
        self.__related_edge_boxes_references_list = related_edge_boxes_references_list

    """"
    end of getters and setters bloc
    """
