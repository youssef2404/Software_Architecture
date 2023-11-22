import threading
import time
import traceback
from src.DataClasses.FormatStatus import FormatCycleState, FormatStop, FormatStopCauseIncident, FormatProduction, \
    FormatEmptyMoldHit, FormatPreproduction, FormatProductionInStop
from src.Environnement.OfStatus import OfStatus
from src.Environnement.OfType import OfType
from src.Environnement.VariablesControl import VariablesControl


class DataSenderToMessagePile:
    def __init__(self, related_edge_box):
        self.related_edge_box = related_edge_box
        self.related_edge_box_reference = self.related_edge_box.get_edge_box_reference()

        self.production_in_stop = 0
        self.production_count = 0
        self.production_not_ok_count = 0
        self.empty_mold_count = 0
        self.preproduction_count = 0

        self.start_stop_timer = None

        self.micro_stop_cause = VariablesControl.micro_stop_cause.value
        self.micro_stop_category = VariablesControl.micro_stop_category.value

        self.end_stop_not_sent = True
        self.begin_stop_not_sent = True

        self.incident_message_not_sent = True
        self.micro_stop_threshold = self.related_edge_box.get_micro_stop_threshold()

        self.logger = self.related_edge_box.logger

    def send_cycle_message(self, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                           machine_id=None, machine_label=None,cycle_state_message=None):

        try:
            self.logger.info("send {} to Line {} from Edge Box: {}"
                             .format(str(cycle_state_message), str(line_label), str(self.related_edge_box_reference)))

            cycle_state = FormatCycleState(lineId=line_id, lineLabel=line_label,
                                           shopFloorWorkShopId=workshop_id, shopFloorWorkShopLabel=workshop_label,
                                           machineId=machine_id, machineRef=machine_label)

            cycle_state_message = cycle_state.get_json_format(cycle_state=cycle_state_message)

            self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(str(cycle_state_message))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_stop_start(self, stop_cause=None, line_id=None, line_label=None, workshop_id=None,
                        workshop_label=None, machine_id=None, machine_label=None, is_of_enabled=False,
                        of_list=None, is_machine_physically_in_stop=None):

        try:
            if is_of_enabled:

                if not of_list:

                    self.logger.info(
                        'No of in line {} for EdgeBox: {}'.
                        format(line_label, str(self.related_edge_box_reference)))
                else:

                    for of in of_list:
                        self.stop_with_of_process(line_id=line_id, line_label=line_label,
                                                  of=of, is_machine_physically_in_stop=is_machine_physically_in_stop,
                                                  stop_cause=stop_cause)
            else:

                self.logger.info(
                    'stop caused by {} started in line {} from EdgeBox: {}'.
                    format(stop_cause, line_label, str(self.related_edge_box_reference)))

                stop_start = FormatStop(lineId=line_id, lineLabel=line_label,
                                        shopFloorWorkShopId=workshop_id, shopFloorWorkShopLabel=workshop_label,
                                        machineId=machine_id, machineRef=machine_label,
                                        is_start_stop=True, incidentLabel=stop_cause, format_choice=False)

                stop_start_message = stop_start.get_json_format()

                self.related_edge_box.get_redis_publisher_to_preprocessing(). \
                    message_pile.append(str(stop_start_message))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_stop_end(self, stop_cause=None, line_id=None, line_label=None, workshop_id=None,
                      workshop_label=None, machine_id=None, machine_label=None, is_of_enabled=False,
                      of_list=None, is_machine_physically_in_stop=None):

        try:
            if is_of_enabled:

                if not of_list:

                    self.logger.info(
                        'No of in line {} for EdgeBox: {}'.
                        format(line_label, str(self.related_edge_box_reference)))
                else:

                    for of in of_list:
                        self.stop_with_of_process(line_id=line_id, line_label=line_label,
                                                  of=of, is_machine_physically_in_stop=is_machine_physically_in_stop,
                                                  stop_cause=stop_cause)
            else:
                self.logger.info(
                    'stop caused by {} ended in Line : {} from EdgeBox : {}'.
                    format(stop_cause, str(line_label), str(self.related_edge_box_reference)))

                end_stop = FormatStop(lineId=line_id, lineLabel=line_label,
                                      shopFloorWorkShopId=workshop_id, shopFloorWorkShopLabel=workshop_label,
                                      machineId=machine_id, machineRef=machine_label,
                                      is_start_stop=False, incidentLabel=stop_cause, format_choice=False)

                end_stop_msg = end_stop.get_json_format()

                self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(str(end_stop_msg))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_show_incident_command(self, line_id=None, line_label=None, of_id=None, stop_cause=None):
        try:
            stop_cause_format = FormatStopCauseIncident(
                lineId=line_id,
                lineLabel=line_label,
                ofId=of_id
            )

            stop_cause_msg = stop_cause_format.get_json_format()

            self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(str(stop_cause_msg))

            self.logger.info(
                'incident caused by {} in line: {} from EdgeBox: {}'.
                format(stop_cause, str(line_label), str(self.related_edge_box_reference)))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_production(self, line_id=None, line_label=None, workshop_id=None, workshop_label=None,
                        machine_id=None, machine_label=None, quantity=None, is_not_ok=None, is_of_enabled=False,
                        of_list=None, is_machine_physically_in_stop=None
                        ):

        try:
            if is_of_enabled:

                threading.Thread(target=self.related_edge_box.detect_unplanned_production,
                                 args=(line_id, line_label)).start()

                """delay for not ok pin to make sure that not ok is active when production is detected"""
                time.sleep(0.1)

                self.related_edge_box.set_mold_state(mold_state=1)

                if not of_list:

                    self.logger.info(
                        'No of in line {} for EdgeBox: {}'.
                        format(line_label, str(self.related_edge_box_reference)))
                else:
                    for of in of_list:
                        self.send_production_with_of_process(line_id=line_id, line_label=line_label,
                                                             workshop_id=workshop_id, workshop_label=workshop_label,
                                                             quantity=quantity, is_not_ok=is_not_ok, of=of,
                                                             is_machine_physically_in_stop=is_machine_physically_in_stop)

            else:

                production = FormatProduction(lineId=str(line_id), lineLabel=line_label,
                                              shopFloorWorkShopId=str(workshop_id),
                                              shopFloorWorkShopLabel=workshop_label,
                                              machineId=str(machine_id),
                                              machineRef=machine_label,
                                              format_choice=False)

                production_message = production.get_json_format(data_quantity=quantity)

                self.production_count += quantity

                self.logger.info("production count = {}".format(self.production_count))

                self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(
                    str(production_message))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_empty_mold(self, line_id=None, line_label=None, of=None, workshop_label=None, workshop_id=None,
                        shopfloor_quantity_by_mold=None):

        try:

            empty_mold_hit = FormatEmptyMoldHit(
                lineId=line_id,
                lineLabel=line_label,
                ofId=of.get_dashboard_of_id(),
                shopFloorWorkShopLabel=workshop_label,
                shopFloorWorkShopId=workshop_id,
                shopFloorQuantityByMold=shopfloor_quantity_by_mold
            )

            empty_mold_hit_msg = empty_mold_hit.get_json_format(data_quantity=1)

            self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(
                str(empty_mold_hit_msg))

            self.empty_mold_count += shopfloor_quantity_by_mold

            self.logger.info("empty mold count {}".
                             format(self.empty_mold_count))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_pre_production(self, line_id=None, line_label=None, of=None, workshop_label=None, workshop_id=None,
                            shopfloor_quantity_by_mold=None):
        try:

            pre_production = FormatPreproduction(
                lineId=line_id,
                lineLabel=line_label,
                ofId=of.get_dashboard_of_id(),
                shopFloorWorkShopLabel=workshop_label,
                shopFloorWorkShopId=workshop_id,
                shopFloorQuantityByMold=shopfloor_quantity_by_mold
            )

            pre_production_msg = pre_production.get_json_format(data_quantity=1)

            self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(str(pre_production_msg))

            self.preproduction_count += shopfloor_quantity_by_mold

            self.logger.info("preproduction count {}".format(self.preproduction_count))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_production_in_stop(self, line_id=None, line_label=None, of=None, workshop_label=None,
                                workshop_id=None, shopfloor_quantity_by_mold=None):

        try:
            production_in_stop = FormatProductionInStop(
                lineId=line_id,
                lineLabel=line_label,
                ofId=of.get_dashboard_of_id(),
                shopFloorWorkShopLabel=workshop_label,
                shopFloorWorkShopId=workshop_id,
                shopFloorQuantityByMold=shopfloor_quantity_by_mold
            )

            production_in_stop_msg = production_in_stop.get_json_format(data_quantity=1)

            self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(
                str(production_in_stop_msg))

            self.production_in_stop += shopfloor_quantity_by_mold

            self.logger.info("production in stop count {}".format(self.production_in_stop))

        except Exception:
            self.logger.error(traceback.format_exc())

    def send_production_with_of_process(self, line_id=None, line_label=None, workshop_id=None,
                                        workshop_label=None, quantity=None, is_not_ok=None, of=None,
                                        is_machine_physically_in_stop=None):
        try:
            """delay to make sure mode qualif is up to date"""
            time.sleep(0.01)

            if is_machine_physically_in_stop:

                if of.get_of_status() == OfStatus.inprogress.value:
                    self.send_empty_mold(line_id=line_id, line_label=line_label, of=of,
                                         workshop_label=workshop_label, workshop_id=workshop_id,
                                         shopfloor_quantity_by_mold=quantity)

            else:

                if of.get_of_status() == OfStatus.inprogress.value:

                    if of.get_of_type() == OfType.cc.value:

                        self.send_pre_production(line_id=line_id, line_label=line_label, of=of,
                                                 workshop_label=workshop_label, workshop_id=workshop_id,
                                                 shopfloor_quantity_by_mold=quantity)

                    elif of.get_of_type() == OfType.production.value and of.get_mode_qualification():

                        self.send_production_in_stop(line_id=line_id, line_label=line_label, of=of,
                                                     workshop_label=workshop_label, workshop_id=workshop_id,
                                                     shopfloor_quantity_by_mold=quantity)

                    elif of.get_of_type() == OfType.production.value and not of.get_mode_qualification():

                        if is_not_ok:
                            production = FormatProduction(
                                lineId=line_id,
                                lineLabel=line_label,
                                ofId=of.get_dashboard_of_id(),
                                shopFloorWorkShopId=workshop_id,
                                shopFloorWorkShopLabel=workshop_label,
                                prodStatus=is_not_ok,
                                shopFloorQuantityByMold=quantity
                            )

                            production_message = production.get_json_format(data_quantity=1)

                            self.production_not_ok_count += quantity

                            self.logger.info(
                                "of : {} not ok count {}".
                                format(of.get_dashboard_of_id(), self.production_not_ok_count))

                        else:

                            production = FormatProduction(
                                lineId=line_id,
                                lineLabel=line_label,
                                ofId=of.get_dashboard_of_id(),
                                shopFloorWorkShopId=workshop_id,
                                shopFloorWorkShopLabel=workshop_label,
                                shopFloorQuantityByMold=quantity,
                                prodStatus=is_not_ok
                            )

                            production_message = production.get_json_format(data_quantity=1)

                            self.production_count += quantity

                            self.logger.info("production count = {}".format(self.production_count))

                        self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(
                            str(production_message))

        except Exception:
            self.logger.error(traceback.format_exc())

    def stop_with_of_process(self, line_id=None, line_label=None, of=None, is_machine_physically_in_stop=None,
                             stop_cause=None):
        try:

            if of.get_of_type() == OfType.production.value \
                    and of.get_of_status() == OfStatus.inprogress.value:

                """stop start *************************************************************************************"""
                if is_machine_physically_in_stop and not of.get_mode_qualification() and self.begin_stop_not_sent:

                    start_stop = FormatStop(
                        lineId=line_id,
                        lineLabel=line_label,
                        ofId=of.get_dashboard_of_id(),
                        is_start_stop=True
                    )

                    stop_start_message = start_stop.get_json_format()

                    self.related_edge_box.get_redis_publisher_to_preprocessing(). \
                        message_pile.append(str(stop_start_message))

                    self.end_stop_not_sent = True
                    self.begin_stop_not_sent = False
                    self.incident_message_not_sent = True

                    of.set_mode_qualification(mode_qualification=True)
                    self.related_edge_box.__incident_popup_shown = False
                    self.start_stop_timer = time.time()

                    self.logger.info(
                        'stop caused by {} started in line {} from EdgeBox: {}'.
                        format(stop_cause, line_label, str(self.related_edge_box_reference)))

                elif not is_machine_physically_in_stop and self.end_stop_not_sent:

                    """
                    stop end ****************************************************************************************** 
                    """
                    if self.start_stop_timer is not None \
                            and time.time() - self.start_stop_timer <= self.micro_stop_threshold:

                        self.logger.info(
                            'stop caused by {} ended in line: {} from EdgeBox: {}'.
                            format(stop_cause, str(line_label), str(self.related_edge_box_reference)))

                        end_stop = FormatStop(
                            lineId=line_id,
                            lineLabel=line_label,
                            ofId=of.get_dashboard_of_id(),
                            is_start_stop=False,
                            incidentLabel=self.micro_stop_cause,
                            incidentCategory=self.micro_stop_category
                        )

                        end_stop_msg = end_stop.get_json_format()

                        self.related_edge_box.get_redis_publisher_to_preprocessing().message_pile.append(
                            str(end_stop_msg))

                        of.set_mode_qualification(mode_qualification=False)
                        self.start_stop_timer = None

                        self.end_stop_not_sent = False
                        self.begin_stop_not_sent = True
                        self.incident_message_not_sent = True

                    elif self.start_stop_timer is not None \
                            and time.time() - self.start_stop_timer > self.micro_stop_threshold:

                        """
                        send incident ********************************************************************************* 
                        """
                        self.incident_message_not_sent = False
                        of.set_stop_cause_specified(stop_cause_specified=False)
                        of.set_mode_qualification(mode_qualification=True)

                        if not self.related_edge_box.__incident_popup_shown:

                            self.related_edge_box.__incident_popup_shown = True

                            self.send_show_incident_command(line_id=line_id,
                                                            line_label=line_label,
                                                            of_id=of.get_dashboard_of_id(),
                                                            stop_cause=stop_cause)
                        else:

                            self.logger.info("stop cause popup already shown")

                        self.end_stop_not_sent = False
                        self.begin_stop_not_sent = True

                        self.logger.debug("stop cause message \n ")

        except Exception:
            self.logger.error(traceback.format_exc())
