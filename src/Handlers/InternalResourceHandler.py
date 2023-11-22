import traceback
import json


class InternalResourceHandler:
    """
    load io_config from configuration_file.json
    such as : host, redis host,  redis password ...
    """

    @staticmethod
    def load_config_from_config_file(config_file_path: str = "", function=(lambda *args, **kwargs: None), config=None):
        try:
            if config_file_path != "" and config is None:
                with open(config_file_path) as config_file:
                    configuration = json.load(config_file)
                return function(configuration)
            else:
                return function(config)

        except Exception:
            traceback.print_exc()
