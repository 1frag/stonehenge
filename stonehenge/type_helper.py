from typing import List, TYPE_CHECKING, Optional, Tuple
from collections import namedtuple

if TYPE_CHECKING:
    import aiopg.sa.result
    import requests_oauthlib
    import aiohttp.web
    import aiopg.sa.engine

    from stonehenge.app import Application
    from stonehenge.users.db_utils import UserInformation

    RowsProxy = List[aiopg.sa.result.RowProxy]
    ResultProxy = aiopg.sa.result.ResultProxy
    OAuth2Session = requests_oauthlib.OAuth2Session

    class Request(aiohttp.web.Request):
        app: Application
        user: UserInformation
