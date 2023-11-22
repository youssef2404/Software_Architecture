import time
import traceback

import threading


class AutomaticPulseThreadSimulation(threading.Thread):
    def __init__(self, input_selection_name, parent_class, holding_duration_total_sec=0, time_between_total_sec=0,
                 total_pulse=0):
        super(AutomaticPulseThreadSimulation, self).__init__()
        self.running = False
        self.input_selection_name = input_selection_name
        self.parent_class = parent_class
        self.ui = self.parent_class.ui

        self.total_pulse = total_pulse
        self.holding_duration_total_sec = holding_duration_total_sec
        self.time_between_total_sec = time_between_total_sec

        if self.parent_class.activeAutomaticPulseThreadSimulation is None or \
                self.parent_class.activeAutomaticPulseThreadSimulation.input_selection_name == \
                self.input_selection_name:
            self.ui.total_pulse.setValue(int(self.total_pulse))
            self.ui.holding_duration_total_sec.setValue(float(self.holding_duration_total_sec))
            self.ui.time_between_total_sec.setValue(float(self.time_between_total_sec))

        self.logger = self.parent_class.logger
        self.paused = True
        self.ui.stop_btn.setDisabled(False)
        self.ui.pause_btn.setDisabled(False)
        self.ui.start_btn.setDisabled(True)

    def run(self):
        try:
            self.paused = False
            self.running = True
            self.ui.stop_btn.setDisabled(False)
            self.ui.pause_btn.setDisabled(False)
            self.ui.start_btn.setDisabled(True)

            if self.input_selection_name != '':
                selected_input = self.input_selection_name
                index = selected_input.index(":")
                selected_input = self.input_selection_name[:index]
                input_checkbox = getattr(self.ui, selected_input)

                if input_checkbox.isChecked():
                    input_checkbox.setChecked(False)

                for i in range(self.total_pulse):
                    if not self.running or self.paused:
                        break

                    input_checkbox.setChecked(True)
                    self.total_pulse = self.total_pulse - 1

                    self.logger.debug('{} {}'.format(self.input_selection_name, self.total_pulse))

                    if self.parent_class.activeAutomaticPulseThreadSimulation == self:
                        self.ui.total_pulse.setValue(int(self.total_pulse))
                    time.sleep(self.holding_duration_total_sec)
                    input_checkbox.setChecked(False)
                    time.sleep(self.time_between_total_sec)

        except Exception:
            self.logger.error(traceback.format_exc())

        finally:
            if not self.paused:
                self.running = False
                self.parent_class.auto_simulation_thread_list.pop(
                    self.parent_class.auto_simulation_thread_list.index(self))

                auto_simulation_thread = AutomaticPulseThreadSimulation(self.input_selection_name, self.parent_class)
                self.parent_class.auto_simulation_thread_list.append(auto_simulation_thread)
                self.ui.stop_btn.setDisabled(False)
                self.ui.pause_btn.setDisabled(False)
                self.ui.start_btn.setDisabled(False)

            else:
                self.running = False

                self.parent_class.auto_simulation_thread_list.pop(
                    self.parent_class.auto_simulation_thread_list.index(self))
                auto_simulation_thread = AutomaticPulseThreadSimulation(self.input_selection_name, self.parent_class,
                                                                        self.holding_duration_total_sec,
                                                                        self.time_between_total_sec, self.total_pulse
                                                                        )

                self.parent_class.auto_simulation_thread_list.append(auto_simulation_thread)
            if self.parent_class.activeAutomaticPulseThreadSimulation == self:
                self.parent_class.activeAutomaticPulseThreadSimulation = auto_simulation_thread

                if self.parent_class.activeAutomaticPulseThreadSimulation.paused:
                    self.ui.pause_btn.setText("Resume")
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
                else:
                    self.ui.pause_btn.setText("Pause")
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
                    self.ui.stop_btn.setDisabled(False)
                    self.ui.pause_btn.setDisabled(False)
                    self.ui.start_btn.setDisabled(False)


