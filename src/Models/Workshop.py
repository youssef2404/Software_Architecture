import traceback


class Workshop:
    """""
    class variable list to save created workshops
    """
    WORKSHOPS_SAVING_LIST = []

    def __init__(self, workshop_id: int, workshop_label: str, creator_line):
        self.__creator_line = creator_line

        self.logger = self.__creator_line.logger

        self.__config_json = self.__creator_line.get_config_json()

        self.__workshop_id = workshop_id
        self.__workshop_label = workshop_label

        self.__workshop_line_list = []

    """""
    get workshop from saving list by id
    """

    @staticmethod
    def get_workshop_by_id(workshop_id):
        try:
            return next((workshop for workshop in Workshop.WORKSHOPS_SAVING_LIST
                         if str(workshop_id) == str(workshop.get_workshop_id())),
                        None)
        except Exception:
            return None

    @staticmethod
    def check_if_workshop_exist(workshop_id):
        try:
            if not any(str(workshop_.get_workshop_id()) == str(workshop_id) for workshop_ in
                       Workshop.WORKSHOPS_SAVING_LIST):
                return False
            else:
                return True
        except:
            return False

    """""
    verify if workshop exist in the saving list (workshop list)
    if not save it
    """

    def save_workshop(self, workshop):
        try:
            if not any(str(salle.get_workshop_id()) == str(workshop.get_workshop_id())
                       for salle in Workshop.WORKSHOPS_SAVING_LIST):
                Workshop.WORKSHOPS_SAVING_LIST.append(workshop)
                return True
            else:
                return False
        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    """
        every workshop can have one or many lines 

        so this function is to affect the lines the their related workshop

        every workshop have a list of lines called workshop_line_list
        """

    def add_lines_to_workshop_lines_list(self, new_line):
        try:
            if not any(line.get_line_id() == new_line.get_line_id()
                       for line in self.get_workshop_line_list()):
                self.get_workshop_line_list().append(new_line)
        except Exception:
            self.logger.error(traceback.format_exc())

    """"
       getters and setters bloc
    """

    def get_workshop_id(self):
        return self.__workshop_id

    def set_workshop_id(self, workshop_id):
        self.__workshop_id = workshop_id

    def get_workshop_label(self):
        return self.__workshop_label

    def set_workshop_label(self, workshop_label):
        self.__workshop_label = workshop_label

    def get_config_json(self):
        return self.__config_json

    def set_config_json(self, config_json):
        self.__config_json = config_json

    def get_workshop_line_list(self):
        return self.__workshop_line_list

    def set_workshop_line_list(self, workshop_line_list):
        self.__workshop_line_list = workshop_line_list

    """"
    end of getters and setters bloc
    """
