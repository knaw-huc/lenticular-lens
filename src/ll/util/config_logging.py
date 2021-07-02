import os
import logging.config


def config_logger():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(levelname)s - %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            },
        },
        'root': {
            'handlers': ['default'],
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'propagate': True
        }
    })
