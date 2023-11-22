import os
import sys
import logging
import logging.handlers
import time
import traceback
from pathlib import Path


class Logger(logging.Logger):
    log_file_directory = None
    log_file_name = None
    log_file_path = None
    is_printing = None
    log_level = None
    rotating_file_handler = None
    Instances = []

    def __init__(self, log_file_directory=None, log_file_name=None, log_level="ERROR",
                 is_printing=False):

        super(Logger, self).__init__(name="SF_Logger")

        Logger.Instances.append(self)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s %(funcName)s %(lineno)d] :  '
                                           '%(message)s', "%Y-%m-%d %H:%M:%S")

        if log_file_directory is not None and log_file_name is not None:
            """initialise from constructor"""
            self.setup_logger_information(log_file_directory=log_file_directory, log_file_name=log_file_name,
                                          log_level=log_level, is_printing=is_printing)

        elif Logger.log_file_name is None:
            self.setup_logger_information(log_level=log_level, is_printing=is_printing)

        elif Logger.log_file_name is not None:
            self.configure_logging_setup()

    def setup_logger_information(self, log_file_directory="", log_file_name="main-SF-Log.log", log_level="ERROR",
                                 is_printing=False):

        if not log_file_directory:
            if getattr(sys, 'frozen', False):
                log_file_directory = os.path.dirname(sys.executable)
            else:
                log_file_directory = os.path.dirname(__file__)

        if not Path(log_file_directory).exists():
            os.mkdir(log_file_directory)

        Logger.log_file_directory = log_file_directory
        Logger.log_file_name = log_file_name

        path_delimiter = '/'

        Logger.log_file_path = path_delimiter.join(
            Logger.log_file_directory.split(path_delimiter) +
            Logger.log_file_name.split(path_delimiter))

        Logger.log_level = log_level
        Logger.is_printing = is_printing

        self.configure_logging_setup()

    def configure_logging_setup(self):
        if not self.handlers:
            self.create_logfile_handlers()
        self.set_is_printing(Logger.is_printing)
        self.set_log_level(Logger.log_level)

    def create_logfile_handlers(self):

        if not Logger.rotating_file_handler:

            rotating_file_handler = logging.handlers.RotatingFileHandler(Logger.log_file_path,
                                                                         maxBytes=10 * (1024 ** 2),
                                                                         backupCount=10,
                                                                         encoding='utf-8')

            rotating_file_handler.setFormatter(self.formatter)
            self.addHandler(rotating_file_handler)
            Logger.rotating_file_handler = rotating_file_handler

        else:
            self.addHandler(Logger.rotating_file_handler)

        """testing timed logger rotating handler"""
        # timed_rotating_file_handler = logging.Handlers.TimedRotatingFileHandler(self.log_file_path,
        #                                                                         when='m', backupCount=2)
        # timed_rotating_file_handler.setFormatter(formatter)
        # self.addHandler(timed_rotating_file_handler)

    def set_log_level(self, log_level: str):
        try:
            for instance in Logger.Instances:
                instance.setLevel(log_level.upper())
                Logger.log_level = log_level.upper()

        except Exception:
            exception_message = traceback.format_exc()
            print(exception_message)
            self.error(exception_message)
            self.setLevel(Logger.log_level)

    def set_is_printing(self, is_printing: bool):

        console_handlers = list(filter(lambda _handler: type(_handler) == logging.StreamHandler, self.handlers))

        if is_printing and not console_handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.formatter)
            self.addHandler(console_handler)

        elif not is_printing and console_handlers:
            for console_handler in console_handlers:
                self.removeHandler(console_handler)

        Logger.is_printing = is_printing

    def addHandler(self, hdlr: logging.Handler) -> None:
        super().addHandler(hdlr=hdlr)
        for instance in Logger.Instances:
            similar_handlers = list(filter(lambda _handler: type(_handler) == type(hdlr), instance.handlers))

            if hdlr not in instance.handlers and not similar_handlers:
                instance.addHandler(hdlr=hdlr)

    def removeHandler(self, hdlr: logging.Handler) -> None:
        super().removeHandler(hdlr=hdlr)

        for instance in Logger.Instances:
            similar_handlers = list(filter(lambda _handler: type(_handler) == type(hdlr), instance.handlers))

            for similar_handler in similar_handlers:
                instance.removeHandler(hdlr=similar_handler)


if __name__ == '__main__':
    """testing logger"""

    if getattr(sys, 'frozen', False):
        execution_root = os.path.dirname(sys.executable)
    else:
        execution_root = os.path.dirname(__file__)

    # logger = Logger(log_file_directory=execution_root + "/log1", log_file_name="main-SF-Log.log",
    #                 log_level="INFO",
    #                 is_printing=True)

    logger = Logger(log_level="info", is_printing=True)
    # logger.setup_logger_information(log_file_directory=execution_root + "/log1", log_file_name="main-SF-Log.log",
    #                                 log_level="info",
    #                                 is_printing=True)

    logger2 = Logger()

    i = 0
    while True:
        i += 1
        logger.info(" logging iteration {} ".format(i))
        logger2.info(" logging iteration {} log 2 ".format(i))
        time.sleep(1)
        if i == 5:
            logger.setLevel("ERROR")
            logger.error("setting up")
            logger.info("info up")
            logger.debug("debugging up")

        if i == 10:
            logger.set_log_level("INFO")
