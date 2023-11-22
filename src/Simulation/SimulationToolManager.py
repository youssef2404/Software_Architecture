import os
import sys
import threading
import time
import traceback
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem

from src.Models.Line import Line
from src.Simulation.MainWindowImpl import MainWindowImpl
from src.Simulation.OpcUaSimulationServer import OpcServerSimulation
from src.Simulation.SfSimulation import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets, QtTest
from src.Simulation.SplashScreen import Ui_Frame
from src.Utilities.Logger import Logger


class SimulationToolManager(threading.Thread):
    def __init__(self, parent_class):
        super(SimulationToolManager, self).__init__()
        if parent_class is not None:
            self.parent_class = parent_class
            self.logger = self.parent_class.logger
        else:
            if getattr(sys, 'frozen', False):
                execution_root = os.path.dirname(sys.executable)
            else:
                execution_root = os.path.dirname(__file__)

            self.parent_class = None
            self.logger = Logger(execution_root, "simulation_log.log", "INFO", True)

        self.ui = Ui_MainWindow()
        self.main_window = None

        self.index = 0

        self.edge_box_references_list = []

        self.console_logger = threading.Thread(target=self.print_log_real_time, args=[self.logger.log_file_path])

        self.ui_loading_complete = False

        self.added_pins_list = []

        self.opc_server_list = []
        self.opc_variable_list = []
        self.opc_server_port = None
        self.opc_server_url = None
        self.splash_screen = None
        self.set_up_ui_completed = threading.Event()
        self.added_opc = threading.Event()
        self.start_splash_screen()

    def start_splash_screen(self):
        try:
            app = QtWidgets.QApplication(sys.argv)
            frame = QtWidgets.QFrame()
            self.splash_screen = Ui_Frame()
            self.splash_screen.setupUi(frame)
            frame.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            frame.show()
            QtTest.QTest.qWait(4000)
            frame.close()
        except:
            self.logger.error(traceback.format_exc())

    def run(self):
        try:
            self.logger.info("QT simulation interface starting")

            app = QtWidgets.QApplication(sys.argv)
            self.main_window = MainWindowImpl(self.parent_class, simulation_tool_manager=self, ui=self.ui)
            self.ui.setupUi(self.main_window)
            self.disable_inputs()
            self.disable_outputs()
            self.ui.clear_log_area.clicked.connect(self.clear_log_area)
            self.ui.edge_box_referencesComboBox.currentIndexChanged.connect(self.edge_box_reference_changed)
            self.set_up_ui_completed.set()

            try:
                self.parent_class.wait_for_edge_box_config.wait()
                self.initialize_opc_ua_server(opc_variable_list=self.opc_variable_list, opc_port=self.opc_server_port)

            except Exception:
                self.logger.error(traceback.format_exc())

            """disable close from simulation window"""
            self.main_window.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
            self.ui.full_menu_widget.hide()
            self.ui.stackedWidget.setCurrentIndex(0)
            self.main_window.show()
            self.ui_loading_complete = True
            self.console_logger.start()
            sys.exit(app.exec_())
        except:
            self.logger.error(traceback.format_exc())

    def set_callback_function(self, pin=None, rising_function=None, falling_function=None, on_change_function=None,
                              type_capteur=None, edge_box_reference=None):
        try:
            self.enable_configured_input(pin=pin, type_capteur=type_capteur, edge_box_reference=edge_box_reference)
            callback_function = {
                'pin': pin,
                'rising_function': rising_function,
                'falling_function': falling_function,
                'on_change_function': on_change_function
            }
            self.main_window.callback_functions_list.append(callback_function)
        except:
            self.logger.error(traceback.format_exc())

    def output(self, pin: int, state: bool):
        try:
            if self.ui is not None:
                output_pin = (getattr(self.ui, 'O_{}'.format(pin)))
                output_pin.setChecked(state)

        except Exception:
            self.logger.error(traceback.format_exc())

    def input(self, pin: int):
        try:
            input_object = getattr(self.ui, 'I_{}'.format(pin))
            state = input_object.isChecked()
            return state
        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    def disable_outputs(self):
        try:
            for pin in range(1, 17):
                output_object = getattr(self.ui, 'O_{}'.format(pin))
                output_object.setDisabled(True)
                output_object.hide()
        except:
            self.logger.error(traceback.format_exc())

    def disable_inputs(self):
        try:
            for pin in range(1, 17):
                input_object = getattr(self.ui, 'I_{}'.format(pin))
                input_object_button = getattr(self.ui, 'I_{}B'.format(pin))
                input_object.setDisabled(True)
                input_object.hide()
                input_object_button.setDisabled(True)
                input_object_button.hide()
        except:
            self.logger.error(traceback.format_exc())

    def enable_configured_input(self, pin, type_capteur, edge_box_reference):
        try:
            if type_capteur is not None:

                pin_old_config = list(
                    filter(lambda callback: int(str(callback['pin'])) == int(str(pin)),
                           self.main_window.callback_functions_list))

                input_object = getattr(self.ui, 'I_{}'.format(pin))
                input_object_button = getattr(self.ui, 'I_{}B'.format(pin))

                input_object.setDisabled(False)
                input_object_button.setDisabled(False)

                input_object.show()
                input_object_button.show()

                self.add_pin_config_to_home_page_table(edge_box_reference, type_capteur, pin, "Tor Entré")

                pin_text = 'I_{} '.format(str(pin))
                if pin_old_config:

                    pin_already_configured = list(
                        filter(lambda pin_config: int(str(pin_config['pin_number'])) == int(str(pin)),
                               self.added_pins_list))

                    if str(type_capteur).lower() != str(pin_already_configured[0]['type_capteur']).lower():
                        input_object.setText(pin_text + str(type_capteur).lower() + " |" +
                                             str(pin_already_configured[0]['type_capteur']).lower())

                else:
                    input_object.setText(pin_text + str(type_capteur).lower())

                self.add_item_to_inputs_list(type_capteur=str(type_capteur).lower(), pin=pin)

                self.add_edge_box_references_to_references_combobox(edge_box_reference=edge_box_reference, pin=pin,
                                                                    type_capteur=type_capteur)
        except:
            self.logger.error(traceback.format_exc())

    def add_item_to_inputs_list(self, type_capteur, pin):
        try:
            item_text = 'I_{}: {}'.format(pin, type_capteur)
            index = self.ui.input_selection.findText(item_text)

            if index == -1:
                self.ui.input_selection.addItem(item_text)
                self.ui.input_selection.setCurrentIndex(-1)
        except:
            self.logger.error(traceback.format_exc())

    def delete_all_items_from_input_list(self):
        try:
            for i in range(self.ui.input_selection.count() - 1, 0, -1):
                self.ui.input_selection.removeItem(i)
        except:
            self.logger.error(traceback.format_exc())

    def add_edge_box_references_to_references_combobox(self, edge_box_reference, pin, type_capteur):
        try:
            pin = {
                'pin_number': pin,
                'type_capteur': type_capteur,
                'edge_box_reference': edge_box_reference
            }
            self.added_pins_list.append(pin)
            if self.edge_box_references_list:
                if edge_box_reference in self.edge_box_references_list:
                    return
                self.edge_box_references_list.append(edge_box_reference)
                self.ui.edge_box_referencesComboBox.addItem(edge_box_reference)
            else:
                self.edge_box_references_list.append(edge_box_reference)
                self.ui.edge_box_referencesComboBox.addItem(edge_box_reference)
        except:
            self.logger.error(traceback.format_exc())

    def output_log_message(self, message):
        try:
            self.ui.log_output.insertPlainText(message + '\n')
        except:
            self.logger.error(traceback.format_exc())
            self.ui.log_output.insertPlainText("output_log_message" + '\n')

    def print_log_real_time(self, logger_path):
        try:
            last_msg = ''
            year = str(datetime.now().strftime("%Y"))
            infinity = 2147483647

            while not self.main_window.isHidden():

                index = 1
                log_file = open(logger_path, "r")
                lines = log_file.readlines()

                if not len(lines):
                    continue

                while not str(lines[-index]).startswith(year):
                    index += 1

                last_lines = lines[-index:]
                message = ' '.join(last_lines)
                scrollbar = self.ui.log_output.verticalScrollBar()

                if message != last_msg:
                    self.output_log_message(message)
                    time.sleep(0.001)
                    scrollbar.setValue(infinity)
                    last_msg = message

                log_file.close()

            self.logger.info("closing print log real time thread")
        except:
            self.logger.error(traceback.format_exc())

    def clear_log_area(self):
        try:
            self.ui.log_output.clear()
        except:
            self.logger.error(traceback.format_exc())

    def edge_box_reference_changed(self):
        try:

            if "All" in self.ui.edge_box_referencesComboBox.currentText():
                self.hide_or_show_all_home_page_table_lines(hide=False)

                for callback_function_affected in self.main_window.callback_functions_list:
                    input_object = getattr(self.ui, 'I_{}'.format(callback_function_affected['pin']))
                    input_object_button = getattr(self.ui, 'I_{}B'.format(callback_function_affected['pin']))
                    input_object.setDisabled(False)
                    input_object.show()
                    input_object_button.setDisabled(False)
                    input_object_button.show()

                self.delete_all_items_from_input_list()

                for pin in self.added_pins_list:
                    self.add_item_to_inputs_list(type_capteur=pin['type_capteur'], pin=pin['pin_number'])

                self.ui.Line_Text.hide()
                self.ui.Line_Label_To_show.hide()

            else:
                self.disable_inputs()
                self.delete_all_items_from_input_list()
                self.hide_or_show_all_home_page_table_lines(hide=True)
                self.show_home_page_table_line_with_edge_box_reference(edge_box_reference=
                                                                       self.ui.edge_box_referencesComboBox.currentText())
                for pin in self.added_pins_list:
                    if pin['edge_box_reference'] == self.ui.edge_box_referencesComboBox.currentText():
                        if str(pin['pin_number']).isnumeric():
                            input_object = getattr(self.ui, 'I_{}'.format(pin['pin_number']))
                            input_object_button = getattr(self.ui, 'I_{}B'.format(pin['pin_number']))
                            input_object.setDisabled(False)
                            input_object.show()
                            input_object_button.setDisabled(False)
                            input_object_button.show()
                            self.add_item_to_inputs_list(type_capteur=pin['type_capteur'], pin=pin['pin_number'])
                            line = Line.get_lines_by_related_edge_box_reference(
                                related_edge_box_reference=pin['edge_box_reference'])
                            if line:
                                self.ui.Line_Text.setText("Line :")
                                self.ui.Line_Text.show()
                                self.ui.Line_Label_To_show.setText(str(line[0].get_line_label()))
                                self.ui.Line_Label_To_show.show()
                        else:
                            line = Line.get_lines_by_related_edge_box_reference(
                                related_edge_box_reference=pin['edge_box_reference'])
                            if line:
                                self.ui.Line_Text.setText("Line :")
                                self.ui.Line_Text.show()
                                self.ui.Line_Label_To_show.setText(str(line[0].get_line_label()))
                                self.ui.Line_Label_To_show.show()
        except:
            self.logger.error(traceback.format_exc())

    def initialize_opc_ua_server(self, server_url="opc.tcp://0.0.0.0:4880/", opc_variable_list=None, opc_port=None):
        try:
            server_port = server_url.split(":")[-1]
            server_port = server_port.split("/")[0]

            if opc_port is not None:
                server_url = server_url.replace(str(server_port), str(opc_port))
                server_port = opc_port

            opc_server_list = list(filter(lambda _opc_server: _opc_server.server_url == server_url,
                                          self.opc_server_list))

            if not len(opc_server_list):
                opc_server = OpcServerSimulation(server_url='opc.tcp://0.0.0.0:{}'.format(server_port))
                self.opc_server_list.append(opc_server)

            else:
                opc_server = opc_server_list[0]

            if opc_variable_list is None:
                opc_variable_list = []

            index = 0
            for opc_variable in opc_variable_list:
                if type(opc_variable) is str:
                    try:
                        self.create_opc_seperator(self.ui)
                        self.add_opc_label(self.ui, opc_variable)
                    except Exception:
                        self.logger.error(traceback.format_exc())
                    continue

                try:
                    index += 1
                    node_id = opc_variable['pin']
                    node_identifier = node_id.split(';')[-1]
                    node_identifier_type = node_identifier.split('=')[0]
                    node_identifier = node_identifier.split('=')[-1]

                    if node_identifier_type.lower() == "i" and node_identifier.isnumeric():
                        node_identifier = int(node_identifier)

                    namespace_index = node_id.split(';')[0]
                    namespace_index = int(namespace_index.split('=')[-1])

                    input_name = opc_variable['typeCapteur']
                    button_label = input_name + ' | ' + node_id

                    try:
                        variable = opc_server.add_variable(node_identifier=node_identifier, initial_value=False,
                                                           is_writable=True,
                                                           namespace_index=namespace_index,
                                                           variable_name=opc_variable['typeCapteur'])
                    except Exception:

                        if 'BadNodeIdExists' in traceback.format_exc():
                            pass
                        else:

                            self.logger.error(traceback.format_exc())

                    self.create_opc_button(index, button_label, self.ui)

                except Exception:
                    self.logger.error(traceback.format_exc())

        except Exception:
            self.logger.error(traceback.format_exc())

    def create_opc_button(self, index, button_label, ui):
        try:
            setattr(ui, "opc_hlayout_{}".format(index), QtWidgets.QHBoxLayout())
            opc_hlayout = getattr(ui, "opc_hlayout_{}".format(index))
            opc_hlayout.setObjectName("opc_hlayout_{}".format(index))

            spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            opc_hlayout.addItem(spacer_item)

            setattr(ui, "opc_btn_{}".format(index), QtWidgets.QPushButton(ui.opc_page))
            opc_btn = getattr(ui, "opc_btn_{}".format(index))
            opc_btn.setObjectName("opc_btn_{}".format(index))
            opc_hlayout.addWidget(opc_btn)

            setattr(ui, "opc_checkbox_{}".format(index), QtWidgets.QCheckBox(ui.opc_page))
            opc_checkbox = getattr(ui, "opc_checkbox_{}".format(index))
            opc_checkbox.setObjectName("opc_checkbox_{}".format(index))
            opc_hlayout.addWidget(opc_checkbox)

            spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            opc_hlayout.addItem(spacer_item)

            setattr(ui, "opc_value_{}".format(index), QtWidgets.QLineEdit(ui.opc_page))
            opc_value_edit = getattr(ui, "opc_value_{}".format(index))
            opc_value_edit.setObjectName("opc_value_{}".format(index))
            opc_value_edit.setPlaceholderText("{} opc value".format(button_label.split(' | ')[0]))
            opc_hlayout.addWidget(opc_value_edit)

            spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            opc_hlayout.addItem(spacer_item)

            ui.opc_layout.addLayout(opc_hlayout)

            opc_btn.setText(button_label)
            opc_checkbox.setText(button_label)

            opc_btn.pressed.connect(opc_checkbox.toggle)
            opc_btn.released.connect(opc_checkbox.toggle)
            opc_checkbox.toggled['bool'].connect(self.main_window.opc_state_changed)

            opc_value_edit.editingFinished.connect(self.main_window.opc_value_changed)

        except Exception:
            self.logger.error(traceback.format_exc())

    def create_opc_seperator(self, ui):
        try:
            horizontal_line = QtWidgets.QFrame(ui.opc_page)
            horizontal_line.setFrameShape(QtWidgets.QFrame.HLine)
            horizontal_line.setFrameShadow(QtWidgets.QFrame.Sunken)
            ui.opc_layout.addWidget(horizontal_line)
        except Exception:
            self.logger.error(traceback.format_exc())

    def add_opc_label(self, ui, text):
        try:
            label = QtWidgets.QLabel(ui.opc_page)
            label.setText(text)
            ui.opc_layout.addWidget(label)
        except Exception:
            self.logger.error(traceback.format_exc())

    def add_pin_config_to_home_page_table(self, edge_reference, type_capteur, pin, type_connex):
        try:
            if not self.verify_if_pin_already_added_to_pins_list(edge_reference=edge_reference, pin_number=pin):
                self.add_edge_box_references_to_references_combobox(edge_box_reference=edge_reference, pin=pin
                                                                    , type_capteur=type_capteur)

            self.ui.edge_affectation_home_page_table.setColumnWidth(1, 250)
            row_count = self.ui.edge_affectation_home_page_table.rowCount()
            self.ui.edge_affectation_home_page_table.insertRow(row_count)
            self.ui.edge_affectation_home_page_table.setItem(row_count, 0, QTableWidgetItem(str(edge_reference)))
            self.ui.edge_affectation_home_page_table.setItem(row_count, 1, QTableWidgetItem(str(type_capteur)))
            self.ui.edge_affectation_home_page_table.setItem(row_count, 2, QTableWidgetItem(str(pin)))
            self.ui.edge_affectation_home_page_table.setItem(row_count, 3, QTableWidgetItem(str(type_connex)))
            for col in range(self.ui.edge_affectation_home_page_table.columnCount()):
                item = self.ui.edge_affectation_home_page_table.item(row_count, col)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Remove the Editable flag

            self.ui.edge_affectation_home_page_table.verticalHeader().setVisible(False)

        except Exception:
            self.logger.error(traceback.format_exc())

    def hide_or_show_all_home_page_table_lines(self, hide=True):
        try:
            for row_to_hide in range(self.ui.edge_affectation_home_page_table.rowCount()):
                self.ui.edge_affectation_home_page_table.setRowHidden(row_to_hide, hide)
        except Exception:
            self.logger.error(traceback.format_exc())

    def show_home_page_table_line_with_edge_box_reference(self, edge_box_reference):
        try:
            for row in range(self.ui.edge_affectation_home_page_table.rowCount()):
                if str(self.ui.edge_affectation_home_page_table.item(row, 0).text()) == str(edge_box_reference):
                    self.ui.edge_affectation_home_page_table.setRowHidden(row, False)
        except Exception:
            self.logger.error(traceback.format_exc())

    def verify_if_pin_already_added_to_pins_list(self, edge_reference, pin_number):
        try:
            for pin in self.added_pins_list:
                if pin['pin_number'] == pin_number and pin['edge_box_reference'] == edge_reference:
                    return True
            return False
        except Exception:
            self.logger.error(traceback.format_exc())
            return False

    def enable_configured_output(self, pin, type_capteur):
        try:

            output_object = getattr(self.ui, 'O_{}'.format(pin))

            output_object.setDisabled(False)

            output_object.show()

            pin_text = "O_{}".format(str(pin))

            output_object.setText(pin_text + " | " + str(type_capteur).lower())

        except:
            self.logger.error(traceback.format_exc())


if __name__ == '__main__':
    try:
        simulationUiThread = SimulationToolManager(None)
        simulationUiThread.start()

    except Exception:
        traceback.print_exc()
