import revpimodio2
import os

root = os.getcwd()  # Defines root as the current working directory


class RevPiIoHandler:

    def __init__(self):
        self.revpi = revpimodio2.RevPiModIO(autorefresh=True, direct_output=True)
        # configrsc=root + r"\src\resources\_config.rsc"
        # , procimg=root + r"\src\resources\piControl0")
        self.revpi.mainloop(blocking=False)

    def set_callback_function(self, pin,
                              rising_function=(lambda *args, **kwargs: None),
                              falling_function=(lambda *args, **kwargs: None),
                              edge_box_reference=(lambda *args, **kwargs: None),
                              type_capteur=(lambda *args, **kwargs: None)
                              ):

        input_object = self.get_input_object(input_number=pin)
        input_object.reg_event(rising_function, edge=revpimodio2.RISING, as_thread=True)
        input_object.reg_event(falling_function, edge=revpimodio2.FALLING, as_thread=True)

    def clean_callback_function(self, pin,
                                rising_function=None,
                                falling_function=None
                                ):

        input_object = self.get_input_object(input_number=pin)
        input_object.unreg_event(rising_function, edge=revpimodio2.RISING, as_thread=True)
        input_object.unreg_event(falling_function, edge=revpimodio2.FALLING, as_thread=True)

    def input(self, pin):
        input_object = self.get_input_object(input_number=pin)
        return input_object.value

    def output(self, pin, state=None):

        output_object = self.get_output_object(output_number=pin)

        if state is not None:
            output_object.value = state
            return output_object.value
        else:
            return output_object.value

    def get_input_object(self, input_number):

        input_list = list(filter(lambda input_obj: input_obj.name == "I_{}".format(input_number), self.revpi.io))

        for input_object in input_list:
            return input_object

    def get_output_object(self, output_number):

        output_list = list(filter(lambda output_obj: output_obj.name == "O_{}".format(output_number), self.revpi.io))

        for output_object in output_list:
            return output_object
