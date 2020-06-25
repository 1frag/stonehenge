from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    import aiopg.sa.result
    import requests_oauthlib
    import aiohttp.web
    import aiopg.sa.engine

    from stonehenge.application.app import Application
    from stonehenge.controllers.ctl_users import UserInformation

    RowsProxy = List[aiopg.sa.result.RowProxy]
    ResultProxy = aiopg.sa.result.ResultProxy
    OAuth2Session = requests_oauthlib.OAuth2Session

    class Request(aiohttp.web.Request):
        app: Application
        user: UserInformation
        to_jinja: dict
