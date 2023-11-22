import traceback

from PyQt5 import QtGui, QtWidgets

from src.Simulation.AutomaticPulseThreadSimulation import AutomaticPulseThreadSimulation


class MainWindowImpl(QtWidgets.QMainWindow):
    def __init__(self, parent_class, simulation_tool_manager, ui):
        super(MainWindowImpl, self).__init__()
        self.paused = False
        self.running = False
        self.activeAutomaticPulseThreadSimulation = None
        self.callback_functions_list = []

        if parent_class is not None:
            self.parent_class = parent_class

        else:
            self.parent_class = simulation_tool_manager

        self.simulation_tool_manager = simulation_tool_manager
        self.logger = self.parent_class.logger
        self.ui = ui

        self.auto_simulation_thread_list = []

    def input_state_changed(self, state):
        try:
            sender_name = self.sender().objectName()
            pin = int(''.join(sender_name.split('I_')))
            matching_callbacks = list(
                filter(lambda callback: int(str(callback['pin'])) == pin, self.callback_functions_list))

            for callback in matching_callbacks:
                if state:
                    if callable(callback['rising_function']):
                        callback['rising_function'](pin=pin, state=state)
                else:
                    if callable(callback['falling_function']):
                        callback['falling_function'](pin=pin, state=state)

        except Exception:
            self.logger.error(traceback.format_exc())

    def closeEvent(self, a0: QtGui.QCloseEvent):
        pass

    def start_prog(self):
        try:
            self.disable_detect_pulse_config_inputs()
            if self.activeAutomaticPulseThreadSimulation is not None:
                self.activeAutomaticPulseThreadSimulation.total_pulse = self.ui.total_pulse.value()
                self.activeAutomaticPulseThreadSimulation.holding_duration_total_sec = \
                    self.ui.holding_duration_total_sec.value()
                self.activeAutomaticPulseThreadSimulation.time_between_total_sec = \
                    self.ui.time_between_total_sec.value()
                self.activeAutomaticPulseThreadSimulation.start()
                if self.activeAutomaticPulseThreadSimulation.paused:
                    self.ui.pause_btn.setText("Resume")
                else:
                    self.ui.pause_btn.setText("Pause")
        except Exception:
            self.logger.error(traceback.format_exc())

    def stop_prog(self, paused=False):
        try:
            self.activeAutomaticPulseThreadSimulation.running = False
            self.ui.total_pulse.setDisabled(False)
            self.ui.holding_duration_total_sec.setDisabled(False)
            self.ui.time_between_total_sec.setDisabled(False)
            self.ui.input_selection.setDisabled(False)
            self.ui.holding_duration_hr.setDisabled(False)
            self.ui.holding_duration_min.setDisabled(False)
            self.ui.holding_duration_sec.setDisabled(False)
            self.ui.time_between_hr.setDisabled(False)
            self.ui.time_between_min.setDisabled(False)
            self.ui.time_between_sec.setDisabled(False)
            self.ui.stop_btn.setDisabled(False)
            self.ui.pause_btn.setDisabled(False)
            self.ui.start_btn.setDisabled(False)
            self.ui.holding_duration_total_sec.setValue(0)
            self.ui.time_between_total_sec.setValue(0)
            self.ui.total_pulse.setValue(0)
        except Exception:
            self.logger.error(traceback.format_exc())

    def pause_prog(self):
        try:
            if self.ui.pause_btn.text() == "Pause":
                self.ui.pause_btn.setText("Resume")
                self.activeAutomaticPulseThreadSimulation.paused = True
                self.paused = True
            else:
                self.paused = False
                self.ui.pause_btn.setText("Pause")
                self.start_prog()
        except Exception:
            self.logger.error(traceback.format_exc())

    def convert_time_between(self, changed_value):
        try:
            sender_name = self.sender().objectName()
            if str(sender_name).endswith("total_sec"):
                seconds_total = self.ui.holding_duration_total_sec.value()
                hr, mn, sec = self.convert_time_format(sec=seconds_total)
                self.ui.holding_duration_hr.setValue(int(hr))
                self.ui.holding_duration_min.setValue(int(mn))
                self.ui.holding_duration_sec.setValue(float(sec))
            else:
                hr = float(self.ui.holding_duration_hr.value())
                mn = float(self.ui.holding_duration_min.value())
                sec = float(self.ui.holding_duration_sec.value())
                seconds_total = self.convert_time_format(hr=hr, mn=mn, sec=sec)
                self.ui.holding_duration_total_sec.setValue(float(seconds_total))
        except Exception:
            self.logger.error(traceback.format_exc())

    def duration_holding(self, changed_value):
        try:
            sender_name = self.sender().objectName()
            if str(sender_name).endswith("total_sec"):
                seconds_total = self.ui.time_between_total_sec.value()
                hr, mn, sec = self.convert_time_format(sec=seconds_total)
                self.ui.time_between_hr.setValue(int(hr))
                self.ui.time_between_min.setValue(int(mn))
                self.ui.time_between_sec.setValue(float(sec))
            else:
                hr = float(self.ui.time_between_hr.value())
                mn = float(self.ui.time_between_min.value())
                sec = float(self.ui.time_between_sec.value())
                seconds_total = self.convert_time_format(hr=hr, mn=mn, sec=sec)
                self.ui.time_between_total_sec.setValue(float(seconds_total))
        except Exception:
            self.logger.error(traceback.format_exc())

    def convert_time_format(self, hr=None, mn=None, sec=None):
        try:
            if sec is None:
                return

            if mn is None and hr is None:
                (hr, mn, sec) = (sec // 3600, (sec % 3600) // 60, sec % 60)
                return hr, mn, sec
            elif mn is not None and hr is not None:
                sec = sec + (mn * 60) + hr * 3600
                return sec

            return None
        except:
            self.logger.error(traceback.format_exc())
            return None

    def changed_input_selection(self):

        input_selection_name = self.sender().currentText()
        self.ui.stop_btn.setDisabled(False)
        self.ui.pause_btn.setDisabled(False)
        self.ui.start_btn.setDisabled(False)
        if input_selection_name == '':
            self.activeAutomaticPulseThreadSimulation = None
            self.ui.stop_btn.setDisabled(False)
            self.ui.pause_btn.setDisabled(False)
            self.ui.start_btn.setDisabled(False)
            return
        else:
            result = list(filter(lambda thread: thread.input_selection_name == input_selection_name,
                                 self.auto_simulation_thread_list))
            if not len(result):

                holding_duration_total_sec = 0
                time_between_total_sec = 0
                total_pulse = 0

                if self.activeAutomaticPulseThreadSimulation is None:
                    holding_duration_total_sec = self.ui.holding_duration_total_sec.value()
                    time_between_total_sec = self.ui.time_between_total_sec.value()
                    total_pulse = self.ui.total_pulse.value()

                automatic_pulse_thread_simulation = AutomaticPulseThreadSimulation(
                    input_selection_name=
                    input_selection_name,
                    parent_class=self,
                    holding_duration_total_sec=holding_duration_total_sec,
                    time_between_total_sec=time_between_total_sec,
                    total_pulse=total_pulse
                )
                self.auto_simulation_thread_list.append(automatic_pulse_thread_simulation)
            else:
                automatic_pulse_thread_simulation = result[0]
                self.ui.total_pulse.setValue(automatic_pulse_thread_simulation.total_pulse)
                self.ui.holding_duration_total_sec.setValue(
                    automatic_pulse_thread_simulation.holding_duration_total_sec)
                self.ui.time_between_total_sec.setValue(automatic_pulse_thread_simulation.time_between_total_sec)

            self.activeAutomaticPulseThreadSimulation = automatic_pulse_thread_simulation

            if self.activeAutomaticPulseThreadSimulation.paused:
                self.ui.pause_btn.setText("Resume")
                self.ui.stop_btn.setDisabled(False)
                self.ui.pause_btn.setDisabled(False)
                self.ui.start_btn.setDisabled(False)
            else:
                self.ui.pause_btn.setText("Pause")
                self.ui.stop_btn.setDisabled(False)
                self.ui.pause_btn.setDisabled(False)
                self.ui.start_btn.setDisabled(False)

            if not self.activeAutomaticPulseThreadSimulation.running:
                self.ui.stop_btn.setDisabled(False)
                self.ui.pause_btn.setDisabled(False)
                self.ui.start_btn.setDisabled(False)
                self.ui.total_pulse.setDisabled(False)
                self.ui.holding_duration_total_sec.setDisabled(False)
                self.ui.time_between_total_sec.setDisabled(False)
                self.ui.input_selection.setDisabled(False)
                self.ui.holding_duration_hr.setDisabled(False)
                self.ui.holding_duration_min.setDisabled(False)
                self.ui.holding_duration_sec.setDisabled(False)
                self.ui.time_between_hr.setDisabled(False)
                self.ui.time_between_min.setDisabled(False)
                self.ui.time_between_sec.setDisabled(False)

            else:
                self.ui.stop_btn.setDisabled(False)
                self.ui.pause_btn.setDisabled(False)
                self.ui.start_btn.setDisabled(True)
                self.ui.total_pulse.setDisabled(True)
                self.ui.holding_duration_total_sec.setDisabled(True)
                self.ui.time_between_total_sec.setDisabled(True)
                self.ui.holding_duration_hr.setDisabled(True)
                self.ui.holding_duration_min.setDisabled(True)
                self.ui.holding_duration_sec.setDisabled(True)
                self.ui.input_selection.setDisabled(False)
                self.ui.time_between_hr.setDisabled(True)
                self.ui.time_between_min.setDisabled(True)
                self.ui.time_between_sec.setDisabled(True)

    def update_thread_values(self):
        pass

    def disable_detect_pulse_config_inputs(self):
        self.ui.total_pulse.setDisabled(True)
        self.ui.holding_duration_total_sec.setDisabled(True)
        self.ui.time_between_total_sec.setDisabled(True)
        self.ui.holding_duration_hr.setDisabled(True)
        self.ui.holding_duration_min.setDisabled(True)
        self.ui.holding_duration_sec.setDisabled(True)
        self.ui.input_selection.setDisabled(False)
        self.ui.time_between_hr.setDisabled(True)
        self.ui.time_between_min.setDisabled(True)
        self.ui.time_between_sec.setDisabled(True)

    def opc_state_changed(self, opc_value=False, sender=None):
        try:
            if sender is None:
                sender = self.sender()
            sender_label = sender.text()

            node_id = str(sender_label).split(' | ')[-1]

            opc_server_list = self.simulation_tool_manager.opc_server_list
            for opc_server in opc_server_list:
                try:
                    node = opc_server.get_node(node_id)
                    node.set_value(opc_value)
                except Exception:
                    pass

        except Exception:
            self.logger.error(traceback.format_exc())

    def opc_value_changed(self):
        try:
            sender_name = self.sender().objectName()
            opc_value = self.sender().text()
            if opc_value == '':
                return
            elif opc_value.isnumeric():
                opc_value = int(opc_value)

            opc_checkbox_index = sender_name.split('_')[-1]
            opc_checkbox = getattr(self.ui, "opc_checkbox_{}".format(opc_checkbox_index))
            self.opc_state_changed(opc_value=opc_value, sender=opc_checkbox)
        except:
            self.logger.error(traceback.format_exc())

    def exit_from_simulation_interface(self):
        try:
            for opc_server in self.simulation_tool_manager.opc_server_list:
                opc_server.kill()
            self.close()
        except:
            self.logger.error(traceback.format_exc())

    def select_opc_page(self):
        try:
            self.ui.stackedWidget.setCurrentIndex(2)
        except:
            self.logger.error(traceback.format_exc())

    def select_io_page(self):
        try:
            self.ui.stackedWidget.setCurrentIndex(1)
            self.ui.tabWidget.setCurrentIndex(0)
        except:
            self.logger.error(traceback.format_exc())

    def select_home_page(self):
        try:
            self.ui.stackedWidget.setCurrentIndex(0)
        except:
            self.logger.error(traceback.format_exc())

    def automatic_pulse_simple_mode(self, state):
        try:
            if state:
                self.ui.holding_duration_total_sec.setValue(float(1))
            else:
                self.ui.holding_duration_total_sec.setValue(float(0))
        except:
            self.logger.error(traceback.format_exc())
