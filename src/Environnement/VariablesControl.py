from enum import Enum


class VariablesControl(Enum):
    time_to_reconnect = 30  # time to reconnect exemple: on opc server (sec)
    stop_duration_limit = 30  # used for type io idle alarm, timed alarm  -->
    # --> and timed unknown alarm  to calculate stop duration
    cycle_production_duration: float = 12  # duration of cycle for cyclic production type io
    duration_of_blinking = 30  # duration of blinking for alarm blinking and stop blinking
    step_of_blinking = 0.2  # step of blinking for alarm blinking and stop blinking
    micro_stop_cause = "Micro Arret"
    micro_stop_category = "Micro Arret"
    micro_stop_threshold = 60 * 1024  # exemple : duration of stop before send incident
    unplanned_production_threshold_value = 5 * 60
