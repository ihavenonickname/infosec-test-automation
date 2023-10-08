import json
import logging
import os
import traceback


LOGGER = logging.getLogger(__name__)

LOGS_DIR = os.environ['LOGS_DIR']


def extra(trace_id: str, **kwargs: object) -> dict[str, object]:
    return {'trace_id': trace_id, 'kwarg': kwargs}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        exc_type, exc_base, exc_stacktrace = None, None, None

        if record.exc_info:
            exc_type = record.exc_info[0].__name__ if record.exc_info[0] else ''
            exc_base = str(record.exc_info[1])
            exc_stacktrace = '\n'.join(traceback.format_tb(record.exc_info[2]))

        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'trace_id': getattr(record, 'trace_id', None),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'kwarg': getattr(record, 'kwarg', None),
            'exc_type': exc_type,
            'exc_base': exc_base,
            'exc_stacktrace': exc_stacktrace,
        })


def configure_log() -> None:
    formatter = JsonFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, 'recon.log')
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)
