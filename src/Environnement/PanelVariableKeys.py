from enum import Enum


class PanelVariableKeys(str, Enum):

    panel_id = "panelId"
    panel_reference = "panelReference"
    affected_pins = "panelAffectPins"

    opc_server_adress = "panelAdrmac"

    line_id = "panelLineId"
    line_label = "panelLineLabel"

    machine_id = "panelMachineId"
    machine_reference = "panelMachineReference"

    post_id = "panelPostId"
    post_reference = "panelPostReference"

    workshop_id = "panelWorkShopId"
    workshop_label = "panelWorkShopLabel"



