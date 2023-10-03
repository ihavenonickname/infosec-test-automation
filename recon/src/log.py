import json
import logging
import os


LOGGER = logging.getLogger(__name__)


def extra(trace_id, **kwargs):
    return {'trace_id': trace_id, 'extra': kwargs}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'trace_id': getattr(record, 'trace_id', None),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'custom_dimensions': getattr(record, 'custom_dimensions', None),
        })


def configure_log():
    formatter = JsonFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    os.makedirs('/logs', exist_ok=True)
    file_handler = logging.FileHandler('/logs/recon.log', mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)
