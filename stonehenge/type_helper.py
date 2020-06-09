from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    import aiopg.sa.result
    import requests_oauthlib
    import aiohttp.web
    import aiopg.sa.engine

    from aiopg.sa.transaction import RootTransaction

    from stonehenge.app import Application

    RowsProxy = List[aiopg.sa.result.RowProxy]
    ResultProxy = aiopg.sa.result.ResultProxy
    OAuth2Session = requests_oauthlib.OAuth2Session

    class Request(aiohttp.web.Request):
        app: Application
