import random
from loguru import logger


def get_proxy() -> str:
    proxy = random.choice(proxies)
    logger.debug(f'Get proxy {proxy}')
    return proxy


proxies = (
    'http://1be90c75da143eedd3d8fe4165447dcea11f669a:js_render=true&antibot=true&window_width=1920&window_height=1080&premium_proxy=true@proxy.zenrows.com:8001',  # noqa
)
