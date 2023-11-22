from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict

"""""
data class to format data before redis publish
"""


def default_data() -> Dict[str, int]:
    return {'quantity': 1}


def default_data_() -> Dict[str, str]:
    return {'type': ''}


@dataclass(order=True)
class FormatProduction:
    shopFloorQuantityByMold: int = 0  # of_quantity_by_mold
    data: Dict[str, int] = field(default_factory=default_data)
    shopFloorType: str = "PRODUCTION"
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    shopFloorPostId: str = None  # post_id
    shopFloorPostLabel: str = None  # post_label
    pin: str = None  # pin
    prodStatus: bool = False  # prodStatus
    ofId: str = ''  # of_reference
    lineLabel: str = ''  # panelLineLabel
    lineId: str = ''  # panelLineId
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    machineRef: str = ''  # machine_label
    machineId: str = ''  # machine_id
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self, data_quantity):
        self.data['quantity'] = int(data_quantity)
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['machineRef']
            del data_to_return['machineId']
            del data_to_return['format_choice']
        else:
            del data_to_return['shopFloorPostId']
            del data_to_return['shopFloorPostLabel']
            del data_to_return['shopFloorQuantityByMold']
            del data_to_return['pin']
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatProductionInStop:
    shopFloorQuantityByMold: int  # of_quantity_by_mold
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    lineLabel: str = ''  # panelLineLabel
    lineId: str = ''  # panelLineId
    ofId: str = ''  # of_reference
    shopFloorPostId: str = None  # post_id
    shopFloorPostLabel: str = None  # post_label
    pin: str = None  # pin
    shopFloorStatus: bool = False
    shopFloorType: str = "PRODUCTIONINSTOP"
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    data: Dict[str, int] = field(default_factory=default_data)
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self, data_quantity):
        self.data['quantity'] = data_quantity
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['format_choice']
        else:
            del data_to_return['shopFloorPostId']
            del data_to_return['shopFloorPostLabel']
            del data_to_return['pin']
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatPreproduction:
    shopFloorQuantityByMold: int  # of_quantity_by_mold
    shopFloorType: str = "PREPRODUCTION"
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    data: Dict[str, int] = field(default_factory=default_data)
    pin: str = None  # pin
    shopFloorPostId: str = None  # post_id
    shopFloorPostLabel: str = None  # post_label
    ofId: str = ''  # of_reference
    lineLabel: str = ''  # panelLineLabel
    lineId: str = ''  # panelLineId
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self, data_quantity):
        self.data['quantity'] = data_quantity
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['format_choice']
        else:
            del data_to_return['shopFloorPostId']
            del data_to_return['shopFloorPostLabel']
            del data_to_return['pin']
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatEmptyMoldHit:
    shopFloorQuantityByMold: int  # of_quantity_by_mold
    shopFloorType: str = "EMPTY_MOLD"
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    data: Dict[str, int] = field(default_factory=default_data)
    pin: str = None  # pin
    shopFloorPostId: str = None  # post_id
    shopFloorPostLabel: str = None  # post_label
    ofId: str = ''  # of_reference
    lineLabel: str = ''  # panelLineLabel
    lineId: str = ''  # panelLineId
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    shopFloorMoldLabel: str = ''  # mold_label
    shopFloorMoldId: str = ''  # mold_id
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self, data_quantity):
        self.data['quantity'] = data_quantity
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['shopFloorMoldId']
            del data_to_return['shopFloorMoldLabel']
            del data_to_return['format_choice']
        else:
            del data_to_return['shopFloorPostId']
            del data_to_return['shopFloorPostLabel']
            del data_to_return['pin']
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatStop:
    machineId: str = ''  # machine_id
    machineRef: str = ''  # machine_label
    is_start_stop: bool = True
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    ofId: str = ''  # of_reference
    lineId: str = ''  # panelLineId
    lineLabel: str = ''  # panelLineLabel
    incidentLabel: str = None  # stop_cause
    incidentCategory: str = None  # stop_category
    comment: str = None  # stop_cause_comment
    responsible: str = None  # stop_cause_responsible
    shopFloorType: str = "STATUS"
    data: Dict[str, str] = field(default_factory=default_data_)
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self):
        if self.is_start_stop:
            # start_arret
            self.data['type'] = 'start'
        else:
            # finish arret
            self.data = {'type': 'finish'}
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['machineId']
            del data_to_return['machineRef']
            del data_to_return['shopFloorWorkShopId']
            del data_to_return['shopFloorWorkShopLabel']
            del data_to_return['is_start_stop']
            del data_to_return['format_choice']
        else:
            del data_to_return['is_start_stop']
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatStopCauseIncident:
    machineId: str = ''  # machine_id
    machineRef: str = ''  # machine_label
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    ofId: str = ''  # of_reference
    lineId: str = ''  # panelLineId
    lineLabel: str = ''  # panelLineLabel
    incidentLabel: str = None  # incidentLabel
    incidentCategory: str = None  # incidentCategory
    data: Dict[str, str] = field(default_factory=default_data_)
    shopFloorType: str = "STATUS"
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self):
        self.data['type'] = 'incident'
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['machineId']
            del data_to_return['machineRef']
            del data_to_return['shopFloorWorkShopId']
            del data_to_return['shopFloorWorkShopLabel']
            del data_to_return['format_choice']
        else:
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatFinCC:
    ofId: str = ''  # of_reference
    lineLabel: str = ''  # panelLineLabel
    lineId: str = ''  # panelLineId
    shopfloorDataCreationTag: str = ''  # creation_tag
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    shopFloorType: str = "CHANGE_CC"
    prodStatus: bool = False
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    data: Dict[str, int] = field(default_factory=default_data)
    format_choice: bool = True  # if true : format with post if false : format with machine

    def get_json_format(self, data_quantity):
        self.data['quantity'] = data_quantity
        data_to_return = asdict(self)
        if self.format_choice:
            del data_to_return['shopFloorWorkShopId']
            del data_to_return['shopFloorWorkShopLabel']
            del data_to_return['format_choice']
        else:
            del data_to_return['format_choice']

        return data_to_return


@dataclass(order=True)
class FormatMachinePhysicalStopJson:
    pin: str
    state: bool

    def get_json_format(self):
        return asdict(self)


@dataclass(order=True)
class FormatUnplannedProduction:
    lineId: str  # panelLineId
    lineLabel: str  # panelLineLabel
    shopFloorType: str = "UNPLANNED_PRODUCTION"
    start: bool = True
    data: Dict[str, str] = field(default_factory=default_data_)
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def get_json_format(self):
        if self.start:
            # run unplanned production
            self.data['type'] = 'start'
        else:
            # finish arret
            self.data['type'] = 'finish'
        return asdict(self)


@dataclass(order=True)
class FormatCycleState:
    machineId: str = ''  # machine_id
    machineRef: str = ''  # machine_label
    lineLabel: str = ''  # line_label
    lineId: str = ''  # line_id
    shopFloorWorkShopId: str = ''  # workshop_id
    shopFloorWorkShopLabel: str = ''  # workshop_label
    ofId: str = ''  # of_id
    dateStart: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dateFinish: str = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    shopFloorType: str = "CYCLE_STATE"
    data: Dict[str, str] = field(default_factory=default_data)

    def get_json_format(self, cycle_state):
        self.data['type'] = cycle_state
        return asdict(self)









