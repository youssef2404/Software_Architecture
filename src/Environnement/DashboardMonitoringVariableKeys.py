from enum import Enum


class DashboardMonitoringVariableKeys(str, Enum):

    line_id = "dashboardLineId"
    of_status = "dashboardStatus"
    of_id = "dashboardOfId"
    of_type = "dashboardType"
    of_mode = "dashboardOfMode"

    of_quantity_by_mold = "dashboardCompQuantityByMold"
    of_product_theoretical_cycle = "dashboardProductTheoreticCycle"
    of_theoretical_cycle_cc = "dashboardDurationCcTheoretic"
    of_creation_tag = "dashboardOfCreationTag"

    workshop_id = "dashboardWorkShopId"
    workshop_label = "dashboardWorkShopLabel"

    mold_label = "ofMoldLabel"
    mold_id = "ofMoldId"






