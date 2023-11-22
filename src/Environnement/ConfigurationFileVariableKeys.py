from enum import Enum


class ConfigurationFileVariableKeys(str, Enum):

    post_processing_port = "Post_processing_port"

    "------------------redis configurations------------------"
    redis_host = "Redis_Host"
    redis_port = "Redis_Port"
    redis_password = "Redis_Password"
    redis_db = "db"

    check_if_of_enabled = "Is_OF_enabled"

    "----------------server dependencies, can be modified by user---------------"
    references_list = "Panel_reference_list"
    log_level = "log_level"
    check_if_simulation_enabled = "simulation"
    console_log = "console_log"
    host = "Host"
