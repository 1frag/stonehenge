import asyncio
from stonehenge.utils.type_helper import *
import logging
import aiohttp.web

logger = logging.getLogger(__name__)


async def streaming(request: 'Request'):
    logger.info(await request.read())
    return aiohttp.web.Response(status=202)
