import threading
import time
import traceback
from functools import partial

from src.DataClasses.FormatStatus import FormatMachinePhysicalStopJson
from src.Environnement.EnumFunctions import EnumFunctions
from src.Environnement.VariablesControl import VariablesControl
from src.Handlers.DataSenderToMessagePile import DataSenderToMessagePile
from src.Models.Machine import Machine
from src.Models.OF import OF
from src.Models.Workshop import Workshop


class TypeIoConfig(threading.Thread):
    def __init__(self, edge_box_reference, related_edge_box):

        super(TypeIoConfig, self).__init__(name=__name__)

        self.related_edge_box = related_edge_box
        self.edge_box_reference = edge_box_reference

        self.logger = self.related_edge_box.logger

        self.machine_physical_stop_list = []

        self.idle_input_state = False
        self.cyclic_production_count = 0

        self.stop_duration_limit_value = VariablesControl.stop_duration_limit.value

        self.is_new_cycle = False
        self.cycle_blinking = False
        self.cycle_started = False

        self.duration_of_blinking = VariablesControl.duration_of_blinking.value
        self.step_of_blinking = VariablesControl.step_of_blinking.value
        self.cycle_production_duration = VariablesControl.cycle_production_duration.value

        self.thread_running = True
        self.unplanned_stop = None

        self.not_ok_state = False

        self.is_of_enabled = self.related_edge_box.get_is_of_enabled()

        self.is_machine_running = True

        self.sender = DataSenderToMessagePile(related_edge_box=self.related_edge_box)

    def get_callback_functions(self, pin_number=None, type_io=None, type_cnx=None, type_capteur=None):

        try:

            related_machine = Machine.get_machine_with_edge_reference_and_affected_pin(related_edge_box_reference=
                                                                                       self.edge_box_reference,
                                                                                       pin_number=pin_number,
                                                                                       type_cnx=type_cnx,
                                                                                       type_capteur=type_capteur,
                                                                                       type_io=type_io
                                                                                       )
            related_line = related_machine.get_affected_line()
            machine_id = related_machine.get_machine_id()
            machine_label = related_machine.get_machine_reference()

            workshop_id = related_line.get_affected_workshop_id()
            workshop = Workshop.get_workshop_by_id(workshop_id=workshop_id)
            workshop_label = workshop.get_workshop_label()

            line_id = related_line.get_line_id()
            line_label = related_line.get_line_label()
            changed_value = self.opc_placeholder_on_value_change_test_type

            rising_function, falling_function = self.generate_callback_functions_by_type_io(line_id, line_label,
                                                                                            machine_id, machine_label,
                                                                                            workshop_id, workshop_label,
                                                                                            type_io,
                                                                                            pin_number,
                                                                                            type_capteur)
            return rising_function, falling_function, changed_value

        except Exception:

            self.logger.error(traceback.format_exc())

    """
    filter type io and return appropriate io_config **********************************************************************
    """

    def generate_callback_functions_by_type_io(self, line_id, line_label, machine_id, machine_label, workshop_id,
                                               workshop_label, type_io, pin_number, type_capteur):

        if "cyclic production" in str(type_io).lower():

            rising_function, falling_function = self.config_type_cyclic_production(

                type_io=type_io, type_capteur=type_capteur, pin_number=pin_number,
                line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                machine_id=machine_id, machine_label=machine_label
            )

        elif 'production cycle state' in str(type_io).lower():

            rising_function, falling_function = self.config_type_production_cycle_state(type_io=type_io,
                                                                                        type_capteur=type_capteur,
                                                                                        pin_number=pin_number,
                                                                                        line_id=line_id,
                                                                                        line_label=line_label,
                                                                                        workshop_id=workshop_id,
                                                                                        workshop_label=workshop_label,
                                                                                        machine_id=machine_id,
                                                                                        machine_label=machine_label)

        elif 'start production cycle' in str(type_io).lower():

            rising_function, falling_function = self.config_type_start_production_cycle(type_io=type_io,
                                                                                        type_capteur=type_capteur,
                                                                                        pin_number=pin_number,
                                                                                        line_id=line_id,
                                                                                        line_label=line_label,
                                                                                        workshop_id=workshop_id,
                                                                                        workshop_label=workshop_label,
                                                                                        machine_id=machine_id,
                                                                                        machine_label=machine_label)

        elif 'end production cycle' in str(type_io).lower():

            rising_function, falling_function = self.config_type_end_production_cycle(type_io=type_io,
                                                                                      type_capteur=type_capteur,
                                                                                      pin_number=pin_number,
                                                                                      line_id=line_id,
                                                                                      line_label=line_label,
                                                                                      workshop_id=workshop_id,
                                                                                      workshop_label=workshop_label,
                                                                                      machine_id=machine_id,
                                                                                      machine_label=machine_label)
        elif "production" in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_production(
                    type_io=type_io, type_capteur=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_production(
                    type_io=type_io, type_capteur=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

        elif 'unknown alarm' in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_unknown_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_unknown_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

        elif "timed alarm" in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_timed_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_timed_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

        elif "idle alarme" in str(type_io).lower():

            rising_function, falling_function = self.config_type_idle_alarm(type_io=type_io, stop_cause=type_capteur,
                                                                            pin_number=pin_number,
                                                                            line_id=line_id, line_label=line_label,
                                                                            workshop_id=workshop_id,
                                                                            workshop_label=workshop_label,
                                                                            machine_id=machine_id,
                                                                            machine_label=machine_label)
        elif "timed unknown alarm" in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_timed_unknown_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_timed_unknown_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

        elif 'alarme blinking' in str(type_io).lower():

            rising_function, falling_function = self.config_type_alarme_blinking(type_io=type_io,
                                                                                 stop_cause=type_capteur,
                                                                                 pin_number=pin_number,
                                                                                 line_id=line_id,
                                                                                 line_label=line_label,
                                                                                 workshop_id=workshop_id,
                                                                                 workshop_label=workshop_label,
                                                                                 machine_id=machine_id,
                                                                                 machine_label=machine_label)

        elif 'alarm' in str(type_io).lower() or "stop" in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_alarm(

                    type_io=type_io, stop_cause=type_capteur, pin_number=pin_number,
                    line_id=line_id, line_label=line_label, workshop_id=workshop_id, workshop_label=workshop_label,
                    machine_id=machine_id, machine_label=machine_label)

        elif 'running' in str(type_io).lower():

            rising_function, falling_function = self.config_type_running(type_io=type_io, type_capteur=type_capteur,
                                                                         pin_number=pin_number,
                                                                         line_id=line_id, line_label=line_label,
                                                                         workshop_id=workshop_id,
                                                                         workshop_label=workshop_label,
                                                                         machine_id=machine_id,
                                                                         machine_label=machine_label)

        elif 'start preparation' in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_start_preparation(type_io=type_io,
                                                                                       type_capteur=type_capteur,
                                                                                       pin_number=pin_number,
                                                                                       line_id=line_id,
                                                                                       line_label=line_label,
                                                                                       workshop_id=workshop_id,
                                                                                       workshop_label=workshop_label,
                                                                                       machine_id=machine_id,
                                                                                       machine_label=machine_label)

            else:

                rising_function, falling_function = self.config_type_start_preparation(type_io=type_io,
                                                                                       type_capteur=type_capteur,
                                                                                       pin_number=pin_number,
                                                                                       line_id=line_id,
                                                                                       line_label=line_label,
                                                                                       workshop_id=workshop_id,
                                                                                       workshop_label=workshop_label,
                                                                                       machine_id=machine_id,
                                                                                       machine_label=machine_label)

        elif 'start cycle' in str(type_io).lower():

            if "reversed" in str(type_io).lower():

                falling_function, rising_function = self.config_type_start_cycle(type_io=type_io,
                                                                                 type_capteur=type_capteur,
                                                                                 pin_number=pin_number,
                                                                                 line_id=line_id,
                                                                                 line_label=line_label,
                                                                                 workshop_id=workshop_id,
                                                                                 workshop_label=workshop_label,
                                                                                 machine_id=machine_id,
                                                                                 machine_label=machine_label
                                                                                 )

            else:

                rising_function, falling_function = self.config_type_start_cycle(type_io=type_io,
                                                                                 type_capteur=type_capteur,
                                                                                 pin_number=pin_number,
                                                                                 line_id=line_id,
                                                                                 line_label=line_label,
                                                                                 workshop_id=workshop_id,
                                                                                 workshop_label=workshop_label,
                                                                                 machine_id=machine_id,
                                                                                 machine_label=machine_label
                                                                                 )

        elif 'cleaning cycle state' in str(type_io).lower():

            rising_function, falling_function = self.config_type_cleaning_cycle_state(type_io=type_io,
                                                                                      type_capteur=type_capteur,
                                                                                      pin_number=pin_number,
                                                                                      line_id=line_id,
                                                                                      line_label=line_label,
                                                                                      workshop_id=workshop_id,
                                                                                      workshop_label=workshop_label,
                                                                                      machine_id=machine_id,
                                                                                      machine_label=machine_label)

        elif 'start cleaning cycle' in str(type_io).lower():

            rising_function, falling_function = self.config_type_start_cleaning_cycle(type_io=type_io,
                                                                                      type_capteur=type_capteur,
                                                                                      pin_number=pin_number,
                                                                                      line_id=line_id,
                                                                                      line_label=line_label,
                                                                                      workshop_id=workshop_id,
                                                                                      workshop_label=workshop_label,
                                                                                      machine_id=machine_id,
                                                                                      machine_label=machine_label)

        elif 'end cleaning cycle' in str(type_io).lower():

            rising_function, falling_function = self.config_type_end_cleaning_cycle(type_io=type_io,
                                                                                    type_capteur=type_capteur,
                                                                                    pin_number=pin_number,
                                                                                    line_id=line_id,
                                                                                    line_label=line_label,
                                                                                    workshop_id=workshop_id,
                                                                                    workshop_label=workshop_label,
                                                                                    machine_id=machine_id,
                                                                                    machine_label=machine_label)

        elif 'cycle state' in str(type_io).lower():

            rising_function, falling_function = self.config_type_cycle_state(type_io=type_io,
                                                                             type_capteur=type_capteur,
                                                                             pin_number=pin_number,
                                                                             line_id=line_id,
                                                                             line_label=line_label,
                                                                             workshop_id=workshop_id,
                                                                             workshop_label=workshop_label,
                                                                             machine_id=machine_id,
                                                                             machine_label=machine_label)

        elif "not ok" in str(type_io).lower():

            rising_function, falling_function = self.config_type_not_ok(pin_number=pin_number)

        elif "ok" == str(type_io).lower():

            rising_function, falling_function = self.config_type_ok(pin_number=pin_number)

        else:

            rising_function = EnumFunctions.empty_function
            falling_function = EnumFunctions.empty_function

            self.logger.info('type Io "{}" not supported'
                             .format(type_io))

        return rising_function, falling_function

    """
    production type io config *****************************************************************************************
    """

    def config_type_production(self, type_io=None, type_capteur=None, pin_number=None,
                               line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                               machine_label=None):

        self.logger.info('input "{}" configured to type IO Production'
                         .format(type_capteur))

        """"
        The functools.partial function allows you to fix certain arguments of a function,
         creating a new function with those arguments already set. In this case, 
         partial fixes the related_line argument to the specified value, 
         and falling_function will hold a reference to the resulting partial function.
        """

        rising_function = partial(self.production_rising, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = self.production_falling

        return rising_function, falling_function

    """production rising callback function"""

    def production_rising(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                          opc_client=None, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                          machine_id=None, machine_label=None, type_capteur=None):
        try:

            of_list = OF.get_of_list_by_edge_box_reference(
                edge_box_reference=self.edge_box_reference)

            threading.Thread(target=self.sender.send_production,
                             kwargs={"line_id": line_id,
                                     "line_label": line_label,
                                     "workshop_id": workshop_id,
                                     "workshop_label": workshop_label,
                                     "quantity": 1,
                                     "is_of_enabled": self.is_of_enabled,
                                     "is_not_ok": self.not_ok_state,
                                     "of_list": of_list,
                                     "machine_id": machine_id,
                                     "machine_label": machine_label,
                                     "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                                     }).start()
        except:
            self.logger.error(traceback.format_exc())

    """production falling callback function"""

    def production_falling(self, pin=None, state=None, data=None, val=None, node=None,
                           opc_client=None, ecb=None):
        time.sleep(0.1)
        try:
            if self.is_of_enabled:
                """fermeture moule"""
                self.related_edge_box.set_mold_state(mold_state=0)
        except Exception:
            self.logger.error(traceback.format_exc())

    """
            detect_machine_state detect the state of the line if there is any stop pin is active:
                if there is pin with state == True -> stop_line = True
                else -> stop_line = False
    """

    def is_machine_physically_in_stop(self):

        try:

            active_stop_pins = list(
                filter(lambda element: (element['state']), self.machine_physical_stop_list))

            if active_stop_pins:
                return True

            return False

        except Exception:
            self.logger.error(traceback.format_exc())

    """
    cyclic production type io config **********************************************************************************
    """

    def config_type_cyclic_production(self, type_io=None, type_capteur=None, pin_number=None,
                                      line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                      machine_id=None,
                                      machine_label=None):

        self.logger.info('input "{}" configured to type IO Cyclic Production'
                         .format(type_capteur))

        rising_function = partial(self.cyclic_production_rising_function, pin_number=pin_number)

        falling_function = EnumFunctions.empty_function

        setattr(self, "cyclic_production_count_{}".format(pin_number).replace(' ', '_'), 0)

        threading.Thread(target=self.cyclic_production_counter,
                         kwargs={"pin": pin_number,
                                 "line_id": line_id,
                                 "line_label": line_label,
                                 "workshop_id": workshop_id,
                                 "workshop_label": workshop_label,
                                 "machine_id": machine_id,
                                 "cycle_duration": self.cycle_production_duration,
                                 "machine_label": machine_label}).start()

        return rising_function, falling_function

    def cyclic_production_rising_function(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                                          node=None, opc_client=None, pin_number=None):

        pin = pin_number
        cyclic_production_count = getattr(self, "cyclic_production_count_{}".format(pin).replace(' ', '_'))
        cyclic_production_count += 1
        setattr(self, "cyclic_production_count_{}".format(pin).replace(' ', '_'), cyclic_production_count)

    def cyclic_production_counter(self, pin, cycle_duration=30, line_id=None, line_label=None,
                                  workshop_id=None, workshop_label=None, machine_id=None, machine_label=None):

        start_cycle_timer = time.time()

        while self.thread_running:
            try:
                if time.time() - start_cycle_timer > cycle_duration:
                    cyclic_production_count = getattr(self,
                                                      "cyclic_production_count_{}".format(pin).replace(' ', '_'))

                    setattr(self, "cyclic_production_count_{}".format(pin).replace(' ', '_'), 0)

                    if cyclic_production_count:
                        of_list = OF.get_of_list_by_edge_box_reference(
                            edge_box_reference=self.edge_box_reference)

                        threading.Thread(target=self.sender.send_production,
                                         kwargs={"line_id": line_id,
                                                 "line_label": line_label,
                                                 "workshop_id": workshop_id,
                                                 "workshop_label": workshop_label,
                                                 "quantity": cyclic_production_count,
                                                 "is_of_enabled": self.is_of_enabled,
                                                 "is_not_ok": self.not_ok_state,
                                                 "of_list": of_list,
                                                 "machine_id": machine_id,
                                                 "machine_label": machine_label,
                                                 "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                                                 }).start()

                    start_cycle_timer = time.time()

                time.sleep(1)
            except Exception:
                self.logger.error(traceback.format_exc())
                time.sleep(1)

    """
    timed alarme type io config *************************************************************************************
    """

    def config_type_timed_alarm(self, type_io=None, stop_cause=None, pin_number=None,
                                line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                                machine_label=None):

        self.logger.info('input "{}" configured to type IO Timed Alarm'
                         .format(stop_cause))

        """ in reversed type send stop if it stays ON for too long"""

        """in normal type send stop if it stays OFF for too long"""

        rising_function = partial(self.timed_alarme_state, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        falling_function = EnumFunctions.empty_function

        return rising_function, falling_function

    def timed_alarme_state(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                           opc_client=None, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                           machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        stop_duration_limit = self.stop_duration_limit_value
        if str(pin_number).isdigit():
            pin = pin_number

            def get_state():
                return self.related_edge_box.io_handler.input(pin)

        else:
            if type(val) is not bool:
                return
            pin = pin_number
            state = val

            def get_state():
                return opc_client.read(pin)

        self.idle_input_state = state

        threading.Thread(target=self.calculate_stop_duration,
                         kwargs={"pin": pin, "stop_state_value": state,
                                 "stop_duration_limit": stop_duration_limit,
                                 "stop_cause": stop_cause,
                                 "update_state": get_state,
                                 "line_id": line_id,
                                 "line_label": line_label,
                                 "workshop_id": workshop_id,
                                 "workshop_label": workshop_label,
                                 "machine_id": machine_id,
                                 "machine_label": machine_label
                                 }).start()

    def calculate_stop_duration(self, pin, stop_state_value, update_state, stop_duration_limit=None, stop_cause='',
                                line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                                machine_label=None):

        if stop_duration_limit is None:
            stop_duration_limit = self.stop_duration_limit_value

        stop_timer = time.time()
        stop_message_sent = False
        resend_stop = False
        idle_input_state = update_state()

        while idle_input_state is stop_state_value:

            idle_input_state = update_state()

            if time.time() - stop_timer > stop_duration_limit \
                    and (resend_stop or not stop_message_sent):
                self.sender.send_stop_start(stop_cause=stop_cause, line_id=line_id,
                                            line_label=line_label, workshop_id=workshop_id,
                                            workshop_label=workshop_label, machine_id=machine_id,
                                            machine_label=machine_label, is_of_enabled=self.is_of_enabled)
                stop_message_sent = True
                resend_stop = False

            if not self.unplanned_stop and self.unplanned_stop is not None and not resend_stop:
                stop_timer = time.time()
                resend_stop = True
                self.unplanned_stop = True

            time.sleep(0.01)

        if stop_message_sent:
            self.sender.send_stop_end(stop_cause=stop_cause, line_id=line_id,
                                      line_label=line_label, workshop_id=workshop_id,
                                      workshop_label=workshop_label, machine_id=machine_id,
                                      machine_label=machine_label)

    """
     idle alarme type io config ***************************************************************************************
    """

    def config_type_idle_alarm(self, type_io=None, stop_cause=None, pin_number=None,
                               line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                               machine_label=None):

        self.logger.info('input "{}" configured to type IO Idle Alarm'
                         .format(stop_cause))

        """send stop if idle for too long"""

        self.idle_input_state = self.related_edge_box.io_handler.input(pin_number)

        rising_function = partial(self.stop_on_idle, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        falling_function = partial(self.stop_on_idle, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        return rising_function, falling_function

    def stop_on_idle(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                     opc_client=None, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                     machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        if str(pin_number).isdigit():
            pin = pin_number

            def get_state():
                return self.related_edge_box.io_handler.input(pin)

        else:
            if type(val) is not bool:
                return
            state = val
            pin = pin_number

            def get_state():
                return opc_client.read(pin)

        self.idle_input_state = state

        threading.Thread(target=self.calculate_stop_duration,
                         kwargs={"pin": pin, "stop_state_value": state,
                                 "update_state": get_state,
                                 "stop_cause": stop_cause,
                                 "line_id": line_id,
                                 "line_label": line_label,
                                 "workshop_id": workshop_id,
                                 "workshop_label": workshop_label,
                                 "machine_id": machine_id,
                                 "machine_label": machine_label
                                 }).start()

    """
        timed unknown alarm type io io_config ***********************************************************************
    """

    def config_type_timed_unknown_alarm(self, type_io=None, stop_cause=None, pin_number=None,
                                        line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                        machine_id=None,
                                        machine_label=None):

        self.logger.info('input "{}" configured to type IO Timed Unknown Alarm'
                         .format(stop_cause))

        """in reversed type send stop if it stays OFF for too long"""
        """in normal type send stop if it stays ON for too long"""

        rising_function = partial(self.timed_unknown_alarme_state, line_id=line_id,
                                  line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id,
                                  workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=stop_cause, pin_number=pin_number)

        falling_function = EnumFunctions.empty_function

        return rising_function, falling_function

    def timed_unknown_alarme_state(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                   opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                   workshop_label=None,
                                   machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        stop_duration_limit = self.stop_duration_limit_value

        if str(pin_number).isdigit():
            pin = pin_number

            def get_state():
                return self.related_edge_box.io_handler.input(pin)

        else:
            if type(val) is not bool:
                return
            state = val
            pin = pin_number

            def get_state():
                return opc_client.read(pin)

        threading.Thread(target=self.calculate_stop_duration,
                         kwargs={"pin": pin, "stop_state_value": state,
                                 "stop_duration_limit": stop_duration_limit,
                                 "stop_cause": "",
                                 "update_state": get_state,
                                 "line_id": line_id,
                                 "line_label": line_label,
                                 "workshop_id": workshop_id,
                                 "workshop_label": workshop_label,
                                 "machine_id": machine_id,
                                 "machine_label": machine_label
                                 }).start()

    """
    running type io io_config ********************************************************************************************
    """

    def config_type_running(self, type_io=None, type_capteur=None, pin_number=None,
                            line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                            machine_label=None):

        self.logger.info('input "{}" configured to type IO Running'
                         .format(type_capteur))

        if str(pin_number).isdigit():
            format_stop = FormatMachinePhysicalStopJson(pin=pin_number, state=True)

            stop_machine_pin = format_stop.get_json_format()

            self.machine_physical_stop_list.append(stop_machine_pin)

        rising_function = partial(self.running_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur, pin_number=pin_number)

        falling_function = partial(self.running_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur, pin_number=pin_number)

        return rising_function, falling_function

    def running_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                            opc_client=None, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                            machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        of_list = OF.get_of_list_by_edge_box_reference(
            edge_box_reference=self.edge_box_reference)

        self.stop_falling(pin=pin_number)

        self.unplanned_stop = False

        threading.Thread(target=self.sender.send_stop_end,
                         kwargs={
                             "stop_cause": type_capteur,
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label,
                             "is_of_enabled": self.is_of_enabled,
                             "of_list": of_list,
                             "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                         }).start()

    def running_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                             opc_client=None, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                             machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        of_list = OF.get_of_list_by_edge_box_reference(
            edge_box_reference=self.edge_box_reference)

        self.stop_rising(pin=pin_number)

        self.unplanned_stop = True

        threading.Thread(target=self.sender.send_stop_start,
                         kwargs={
                             "stop_cause": type_capteur,
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label,
                             "is_of_enabled": self.is_of_enabled,
                             "of_list": of_list,
                             "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                         }).start()

    """
    alarme type io io_config *********************************************************************************************
    """

    def config_type_alarm(self, type_io=None, stop_cause=None, pin_number=None,
                          line_id=None, line_label=None, workshop_id=None, workshop_label=None, machine_id=None,
                          machine_label=None):

        self.logger.info('input "{}" configured to type IO Alarm'
                         .format(stop_cause))

        if str(pin_number).isdigit():
            format_stop = FormatMachinePhysicalStopJson(pin=pin_number, state=False)

            stop_machine_pin = format_stop.get_json_format()

            self.machine_physical_stop_list.append(stop_machine_pin)

        rising_function = partial(self.alarm_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id,
                                  workshop_id=workshop_id,
                                  workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        falling_function = partial(self.alarm_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id,
                                   workshop_id=workshop_id,
                                   workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        return rising_function, falling_function

    def alarm_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                          opc_client=None, line_id=None, line_label=None, workshop_id=None,
                          workshop_label=None,
                          machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        of_list = OF.get_of_list_by_edge_box_reference(
            edge_box_reference=self.edge_box_reference)

        self.stop_rising(pin=pin_number)

        threading.Thread(target=self.sender.send_stop_start,
                         kwargs={
                             "stop_cause": stop_cause,
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label,
                             "is_of_enabled": self.is_of_enabled,
                             "of_list": of_list,
                             "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                         }).start()

    def alarm_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                           opc_client=None, line_id=None, line_label=None, workshop_id=None,
                           workshop_label=None,
                           machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        of_list = OF.get_of_list_by_edge_box_reference(
            edge_box_reference=self.edge_box_reference)

        self.stop_falling(pin=pin_number)

        threading.Thread(target=self.sender.send_stop_end,
                         kwargs={
                             "stop_cause": stop_cause,
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label,
                             "is_of_enabled": self.is_of_enabled,
                             "of_list": of_list,
                             "is_machine_physically_in_stop": self.is_machine_physically_in_stop()
                         }).start()

    """stop rising callback function for stop pin(typeIo = stop)"""

    def stop_rising(self, ecb=None, pin=None, state=None):

        try:

            if ecb is not None:
                pin = int(ecb.ioname.split('_')[-1])

            self.update_machine_physical_stop_state(str(pin), True)

        except Exception:
            self.logger.error(traceback.format_exc())

    """stop falling callback function for stop pin(typeIo = stop)"""

    def stop_falling(self, ecb=None, pin=None, state=None):
        try:

            if ecb is not None:
                pin = int(ecb.ioname.split('_')[-1])

            self.update_machine_physical_stop_state(str(pin), False)

        except Exception:
            self.logger.error(traceback.format_exc())

    """
            update the state of pin that could stop the affected_line(typeIo: stop/ typeIo: Alarm)
            the state of pin is updated in the dictionary self.related_edge_box_machine_in_stop
            self.related_edge_box_machine_in_stop contain all pin that could stop the __affected_line
            for each pin is indicated {pin/state}
    """

    def update_machine_physical_stop_state(self, pin, state):

        try:
            if self.machine_physical_stop_list:

                stop_pins = list(filter(lambda element: (int(element['pin']) == int(pin)),
                                        self.machine_physical_stop_list))

                for stop_pin in stop_pins:
                    self.machine_physical_stop_list.remove(stop_pin)
                    stop_pin['state'] = state
                    self.machine_physical_stop_list.append(stop_pin)
                    self.logger.info("machine_physical_stop {} ".format(self.machine_physical_stop_list))

                if not stop_pins:
                    self.logger.error("Pin {} not configured in machine_physical_stop storage {}"
                                      .format(pin, self.machine_physical_stop_list))

        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error("error updating stop pin {} state to {}".format(pin, state))

    """        
    unknown alarm type io config *******************************************************************************
    """

    def config_type_unknown_alarm(self, type_io=None, stop_cause=None, pin_number=None,
                                  line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                  machine_id=None,
                                  machine_label=None):

        self.logger.info('input "{}" configured to type IO Unknown Alarm'
                         .format(stop_cause))

        rising_function = partial(self.unknown_alarm_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id,
                                  workshop_id=workshop_id,
                                  workshop_label=workshop_label, stop_cause=stop_cause)

        falling_function = partial(self.unknown_alarm_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id,
                                   workshop_id=workshop_id,
                                   workshop_label=workshop_label, stop_cause=stop_cause)

        return rising_function, falling_function

    def unknown_alarm_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                  opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                  workshop_label=None,
                                  machine_id=None, machine_label=None, stop_cause=None):

        threading.Thread(target=self.sender.send_stop_start,
                         kwargs={
                             "stop_cause": "",
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label,
                             "is_of_enabled": self.is_of_enabled
                         }).start()

    def unknown_alarm_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                   opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                   workshop_label=None,
                                   machine_id=None, machine_label=None, stop_cause=None):

        threading.Thread(target=self.sender.send_stop_end,
                         kwargs={
                             "stop_cause": "",
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label
                         }).start()

    """        
    start preparation type io config **********************************************************************************
    """

    def config_type_start_preparation(self, type_io=None, type_capteur=None, pin_number=None,
                                      line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                      machine_id=None,
                                      machine_label=None):

        self.logger.info('input "{}" configured to type IO Start Preparation'
                         .format(type_capteur))

        rising_function = partial(self.start_preparation_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id,
                                  workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = self.start_preparation_falling_edge

        return rising_function, falling_function

    def start_preparation_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                      opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                      workshop_label=None,
                                      machine_id=None, machine_label=None, type_capteur=None):

        threading.Thread(target=self.sender.send_cycle_message,
                         kwargs={

                             "cycle_state_message": 'Debut preparation',
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label

                         }).start()

        self.is_new_cycle = True

    def start_preparation_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                       opc_client=None):

        self.is_new_cycle = False

    """
    start cycle type io config ****************************************************************************************
    """

    def config_type_start_cycle(self, type_io=None, type_capteur=None, pin_number=None,
                                line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                machine_id=None,
                                machine_label=None, opc_client=None):

        self.logger.info('input "{}" configured to type IO Start Cycle'
                         .format(type_capteur))

        rising_function = []
        falling_function = []

        rising_function.append(partial(self.start_cycle_rising_edge, line_id=line_id, line_label=line_label,
                                       machine_label=machine_label, machine_id=machine_id,
                                       workshop_id=workshop_id,
                                       workshop_label=workshop_label, type_capteur=type_capteur))

        falling_function.append(EnumFunctions.empty_function)

        rising_function.append(partial(self.running_rising_edge, line_id=line_id, line_label=line_label,
                                       machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                       workshop_label=workshop_label, type_capteur=type_capteur,
                                       pin_number=pin_number))

        falling_function.append(partial(self.running_falling_edge, line_id=line_id, line_label=line_label,
                                        machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                        workshop_label=workshop_label, type_capteur=type_capteur,
                                        pin_number=pin_number))

        if str(pin_number).isdigit():
            self.is_machine_running = self.related_edge_box.io_handler.input(pin_number)

        else:
            if opc_client is not None:
                node_id = pin_number
                self.is_machine_running = opc_client.read(node_id)

        if type(self.is_machine_running) is not bool:
            self.is_machine_running = False

        return rising_function, falling_function

    def start_cycle_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                workshop_label=None,
                                machine_id=None, machine_label=None, type_capteur=None):

        if self.is_new_cycle:
            self.is_new_cycle = False
            threading.Thread(target=self.sender.send_cycle_message,
                             kwargs={
                                 "cycle_state_message": 'Start production cycle',
                                 "line_id": line_id,
                                 "line_label": line_label,
                                 "workshop_id": workshop_id,
                                 "workshop_label": workshop_label,
                                 "machine_id": machine_id,
                                 "machine_label": machine_label
                             }).start()

    """
       production cycle state type io config **************************************************************************
    """

    def config_type_production_cycle_state(self, type_io=None, type_capteur=None, pin_number=None,
                                           line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                           machine_id=None,
                                           machine_label=None):

        self.logger.info('input "{}" configured to type IO Production Cycle State'
                         .format(type_capteur))

        rising_function = partial(self.cycle_state_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = partial(self.cycle_state_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur)

        return rising_function, falling_function

    def cycle_state_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                workshop_label=None,
                                machine_id=None, machine_label=None, type_capteur=None):

        # send_cycle_start
        threading.Thread(target=self.sender.send_cycle_message,
                         kwargs={
                             "cycle_state_message": 'Start production cycle',
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label
                         }).start()

    def cycle_state_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                 opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                 workshop_label=None,
                                 machine_id=None, machine_label=None, type_capteur=None):

        # send_cycle_end
        threading.Thread(target=self.sender.send_cycle_message,
                         kwargs={
                             "cycle_state_message": 'End production cycle',
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label
                         }).start()

    """
       start production cycle type io config **************************************************************************
    """

    def config_type_start_production_cycle(self, type_io=None, type_capteur=None, pin_number=None,
                                           line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                           machine_id=None,
                                           machine_label=None):

        self.logger.info('input "{}" configured to type IO Start Production Cycle'
                         .format(type_capteur))

        rising_function = partial(self.cycle_state_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = EnumFunctions.empty_function

        return rising_function, falling_function

    """
        end production cycle type io config *************************************************************************
    """

    def config_type_end_production_cycle(self, type_io=None, type_capteur=None, pin_number=None,
                                         line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                         machine_id=None,
                                         machine_label=None):

        self.logger.info('input "{}" configured to type IO End Production Cycle'
                         .format(type_capteur))

        rising_function = EnumFunctions.empty_function

        falling_function = partial(self.cycle_state_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur)

        return rising_function, falling_function

    """
        cleaning cycle state type io config **************************************************************************
    """

    def config_type_cleaning_cycle_state(self, type_io=None, type_capteur=None, pin_number=None,
                                         line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                         machine_id=None,
                                         machine_label=None):

        self.logger.info('input "{}" configured to type IO Cleaning Cycle State'
                         .format(type_capteur))

        rising_function = partial(self.cleaning_cycle_state_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = partial(self.cleaning_cycle_state_rising_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur)

        return rising_function, falling_function

    def cleaning_cycle_state_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None, node=None,
                                         opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                         workshop_label=None,
                                         machine_id=None, machine_label=None, type_capteur=None):

        # send_cleaning_cycle_start
        threading.Thread(target=self.sender.send_cycle_message,
                         kwargs={
                             "cycle_state_message": 'Start cleaning cycle',
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label
                         }).start()

    """
        start cleaning cycle type io config **************************************************************************
    """

    def config_type_start_cleaning_cycle(self, type_io=None, type_capteur=None, pin_number=None,
                                         line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                         machine_id=None,
                                         machine_label=None):

        self.logger.info('input "{}" configured to type IO Start Cleaning Cycle'
                         .format(type_capteur))

        rising_function = partial(self.cleaning_cycle_state_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur)

        falling_function = EnumFunctions.empty_function

        return rising_function, falling_function

    """
        end_cleaning_cycle type io config ****************************************************************************
    """

    def config_type_end_cleaning_cycle(self, type_io=None, type_capteur=None, pin_number=None,
                                       line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                       machine_id=None,
                                       machine_label=None):

        self.logger.info('input "{}" configured to type IO End Cleaning Cycle'
                         .format(type_capteur))

        rising_function = EnumFunctions.empty_function

        falling_function = partial(self.cleaning_cycle_state_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur)

        return rising_function, falling_function

    def cleaning_cycle_state_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                                          node=None,
                                          opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                          workshop_label=None,
                                          machine_id=None, machine_label=None, type_capteur=None):

        # send_cleaning_cycle_end
        threading.Thread(target=self.sender.send_cycle_message,
                         kwargs={
                             "cycle_state_message": 'End cleaning cycle',
                             "line_id": line_id,
                             "line_label": line_label,
                             "workshop_id": workshop_id,
                             "workshop_label": workshop_label,
                             "machine_id": machine_id,
                             "machine_label": machine_label
                         }).start()

    """
      cycle state type io config ************************************************************************************
    """

    def config_type_cycle_state(self, type_io=None, type_capteur=None, pin_number=None,
                                line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                machine_id=None,
                                machine_label=None):

        self.logger.info('input "{}" configured to type IO Cycle State'
                         .format(type_capteur))

        rising_function = partial(self.cycle_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, type_capteur=type_capteur, pin_number=pin_number)

        falling_function = partial(self.cycle_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, type_capteur=type_capteur, pin_number=pin_number)

        return rising_function, falling_function

    def cycle_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                          node=None,
                          opc_client=None, line_id=None, line_label=None, workshop_id=None,
                          workshop_label=None,
                          machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        threading.Thread(target=self.cycle_changed_state, kwargs={"pin_number": pin_number, "state": state,
                                                                  "line_id": line_id,
                                                                  "line_label": line_label,
                                                                  "workshop_id": workshop_id,
                                                                  "workshop_label": workshop_label,
                                                                  "machine_id": machine_id,
                                                                  "machine_label": machine_label}).start()

    def cycle_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                           node=None,
                           opc_client=None, line_id=None, line_label=None, workshop_id=None,
                           workshop_label=None,
                           machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        threading.Thread(target=self.cycle_changed_state, kwargs={"pin_number": pin_number, "state": state,
                                                                  "line_id": line_id,
                                                                  "line_label": line_label,
                                                                  "workshop_id": workshop_id,
                                                                  "workshop_label": workshop_label,
                                                                  "machine_id": machine_id,
                                                                  "machine_label": machine_label}).start()

    def cycle_changed_state(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                            node=None,
                            opc_client=None, line_id=None, line_label=None, workshop_id=None,
                            workshop_label=None,
                            machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        if self.check_cycle_blinking(pin_number=pin_number, state=state, line_id=line_id, line_label=line_label,
                                     workshop_id=workshop_id,
                                     workshop_label=workshop_label, machine_id=machine_id,
                                     machine_label=machine_label):
            return

        '''input is stable'''

        self.cycle_blinking = False

        if state:
            if not self.cycle_started:
                # send_cycle_start
                self.sender.send_cycle_message(line_id=line_id, line_label=line_label, workshop_id=workshop_id,
                                               workshop_label=workshop_label, machine_id=machine_id,
                                               machine_label=machine_label, cycle_state_message='Debut cycle')
            self.cycle_started = True

        else:
            if self.cycle_started:
                # send_cycle_end
                self.sender.send_cycle_message(line_id=line_id, line_label=line_label, workshop_id=workshop_id,
                                               workshop_label=workshop_label, machine_id=machine_id,
                                               machine_label=machine_label, cycle_state_message='Fin cycle')

            self.cycle_started = False

    def check_cycle_blinking(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                             node=None,
                             opc_client=None, line_id=None, line_label=None, workshop_id=None,
                             workshop_label=None,
                             machine_id=None, machine_label=None, type_capteur=None, pin_number=None):

        pin = pin_number

        duration = self.duration_of_blinking
        step = self.step_of_blinking

        for iteration in range(int(duration / step)):

            time.sleep(step)

            if type(pin) is int:
                new_state = self.related_edge_box.io_handler.input(pin)

            else:
                return

            if new_state is not state:
                '''input is blinking'''

                if not self.cycle_blinking:
                    # send_cycle_ready
                    self.sender.send_cycle_message(line_id=line_id, line_label=line_label, workshop_id=workshop_id,
                                                   workshop_label=workshop_label, machine_id=machine_id,
                                                   machine_label=machine_label, cycle_state_message='Dosage pret')

                self.cycle_blinking = True
                return True
        return False

    """
       alarme blinking type io config *********************************************************************************
    """

    def config_type_alarme_blinking(self, type_io=None, stop_cause=None, pin_number=None,
                                    line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                                    machine_id=None,
                                    machine_label=None):

        self.logger.info('input "{}" configured to type IO Alarm Blinking'
                         .format(stop_cause))

        rising_function = partial(self.blinking_stop_rising_edge, line_id=line_id, line_label=line_label,
                                  machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                  workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        falling_function = partial(self.blinking_stop_falling_edge, line_id=line_id, line_label=line_label,
                                   machine_label=machine_label, machine_id=machine_id, workshop_id=workshop_id,
                                   workshop_label=workshop_label, stop_cause=stop_cause, pin_number=pin_number)

        setattr(self, 'stop_blinking_{}'.format(pin_number), False)

        return rising_function, falling_function

    def blinking_stop_rising_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                                  node=None,
                                  opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                  workshop_label=None,
                                  machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        if str(pin_number).isdigit():
            threading.Thread(target=self.stop_changed_sate, kwargs={"pin_number": pin_number, "state": state,
                                                                    "line_id": line_id,
                                                                    "line_label": line_label,
                                                                    "workshop_id": workshop_id,
                                                                    "workshop_label": workshop_label,
                                                                    "machine_id": machine_id,
                                                                    "machine_label": machine_label,
                                                                    "stop_cause": stop_cause}).start()
        else:
            pin = node
            state = val
            threading.Thread(target=self.stop_changed_sate, kwargs={"pin_number": pin, "state": state,
                                                                    "line_id": line_id,
                                                                    "line_label": line_label,
                                                                    "workshop_id": workshop_id,
                                                                    "workshop_label": workshop_label,
                                                                    "machine_id": machine_id,
                                                                    "machine_label": machine_label,
                                                                    "stop_cause": stop_cause,
                                                                    "opc_client": opc_client}).start()

    def blinking_stop_falling_edge(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                                   node=None,
                                   opc_client=None, line_id=None, line_label=None, workshop_id=None,
                                   workshop_label=None,
                                   machine_id=None, machine_label=None, stop_cause=None, pin_number=None):
        if str(pin_number).isdigit():
            threading.Thread(target=self.stop_changed_sate, kwargs={"pin_number": pin_number, "state": state,
                                                                    "line_id": line_id,
                                                                    "line_label": line_label,
                                                                    "workshop_id": workshop_id,
                                                                    "workshop_label": workshop_label,
                                                                    "machine_id": machine_id,
                                                                    "machine_label": machine_label,
                                                                    "stop_cause": stop_cause}).start()
        else:
            pin = node
            state = val
            threading.Thread(target=self.stop_changed_sate, kwargs={"pin_number": pin, "state": state,
                                                                    "line_id": line_id,
                                                                    "line_label": line_label,
                                                                    "workshop_id": workshop_id,
                                                                    "workshop_label": workshop_label,
                                                                    "machine_id": machine_id,
                                                                    "machine_label": machine_label,
                                                                    "stop_cause": stop_cause,
                                                                    "opc_client": opc_client}).start()

    def stop_changed_sate(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                          node=None,
                          opc_client=None, line_id=None, line_label=None, workshop_id=None,
                          workshop_label=None,
                          machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        if self.check_stop_blinking(pin_number=pin_number, state=state, line_id=line_id, line_label=line_label,
                                    workshop_id=workshop_id,
                                    workshop_label=workshop_label, machine_id=machine_id,
                                    machine_label=machine_label, stop_cause=stop_cause, opc_client=opc_client):
            return

        '''input is stable'''
        setattr(self, 'stop_blinking_{}'.format(pin_number), False)
        if state:
            pass
        else:
            self.sender.send_stop_end(stop_cause=stop_cause,
                                      line_id=line_id,
                                      line_label=line_label,
                                      workshop_id=workshop_id,
                                      workshop_label=workshop_label,
                                      machine_id=machine_id,
                                      machine_label=machine_label)

    def check_stop_blinking(self, pin=None, state=None, eventcallback=None, data=None, val=None,
                            node=None,
                            opc_client=None, line_id=None, line_label=None, workshop_id=None,
                            workshop_label=None,
                            machine_id=None, machine_label=None, stop_cause=None, pin_number=None):

        pin = pin_number

        duration = self.duration_of_blinking
        step = self.step_of_blinking

        for iteration in range(int(duration / step)):
            time.sleep(step)

            if str(pin).isnumeric():
                new_state = self.related_edge_box.io_handler.input(pin)

            elif not str(pin).isnumeric() and "ns" in str(pin):
                new_state = opc_client.read(pin)

            else:
                return

            if new_state is not state:
                '''input is blinking'''

                stop_blinking = getattr(self, 'stop_blinking_{}'.format(pin))

                if not stop_blinking:
                    self.sender.send_stop_start(stop_cause=stop_cause,
                                                line_id=line_id, line_label=line_label,
                                                workshop_id=workshop_id, workshop_label=workshop_label,
                                                machine_id=machine_id, machine_label=machine_label,
                                                is_of_enabled=self.is_of_enabled)

                setattr(self, 'stop_blinking_{}'.format(pin), True)

                return True
        return False

    """
      not ok type io config ****************************************************************************************
    """

    def config_type_not_ok(self, pin_number):
        rising_function = self.not_ok_state_rising
        falling_function = self.not_ok_state_falling

        if self.related_edge_box.io_handler.input(pin_number):

            self.not_ok_state_rising()

        else:

            self.not_ok_state_falling()

        return rising_function, falling_function

    """Not ok rising callback function for pin(typeIo = not ok)"""

    def not_ok_state_rising(self, pin=None, state=None, ecb=None):
        try:

            self.not_ok_state = True

        except Exception:

            self.logger.error(traceback.format_exc())

    """Not ok falling callback function for pin(typeIo =not ok)"""

    def not_ok_state_falling(self, pin=None, state=None, ecb=None):
        try:

            self.not_ok_state = False

        except Exception:
            self.logger.error(traceback.format_exc())

    """
    ok type io config ************************************************************************************************    
    """

    def config_type_ok(self, pin_number):
        rising_function = self.ok_state_rising
        falling_function = self.ok_state_falling

        if self.related_edge_box.io_handler.input(pin_number):

            self.ok_state_rising()

        else:

            self.ok_state_falling()

        return rising_function, falling_function

    """ok rising callback function for pin(typeIo = ok)"""

    def ok_state_rising(self, pin=None, state=None, ecb=None):
        try:

            self.not_ok_state = False

        except Exception:

            self.logger.error(traceback.format_exc())

    """ok falling callback function for pin(typeIo = ok)"""

    def ok_state_falling(self, pin=None, state=None, ecb=None):
        try:

            self.not_ok_state = True

        except Exception:
            self.logger.error(traceback.format_exc())

    """
        opc placeholder on value change test type ioconfig ******************************************************    
    """
    """
    this type io was added just for test
    test placeholder on change value in opc io_config
    """

    def opc_placeholder_on_value_change_test_type(self, pin=None, state=None, data=None, val=None, node=None,
                                                  opc_client=None):
        self.logger.info("new placeholder value = {}".format(val))
