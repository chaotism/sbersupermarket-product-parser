import logging
import loguru
from starlette_context import context


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def app_request_context_log_middleware_patcher(record: 'loguru.Record'):
    record = record.copy()
    if context.exists():
        record['extra']['correlation_id'] = context.data['X-Correlation-ID']
        record['extra']['request_id'] = context.data['X-Request-ID']
        return

    record['extra']['correlation_id'] = 'undefined'
    record['extra']['request_id'] = 'undefined'


def setup_logging(debug: bool = True):
    log_format = (
        '{time} '
        '| {level} '
        '| {name}:{module}:{line}'
        '| request_id:{extra[request_id]} correlation_id:{extra[correlation_id]}'
        '| {message} {exception}'
    )
    loguru.logger.configure(
        handlers=[
            dict(
                sink=print,
                level='DEBUG',
                colorize=True,
                serialize=False,
            )
            if debug
            else dict(
                sink=lambda v: print(v.replace('\n', ' ') + '\n'),
                format=log_format,
                level='INFO',
                colorize=False,
                serialize=False,
                backtrace=False,
                diagnose=False,
            ),
        ],
        patcher=app_request_context_log_middleware_patcher,
    )
    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel('DEBUG' if debug else 'INFO')
