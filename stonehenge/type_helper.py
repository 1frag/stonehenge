from typing import List
import aiopg.sa.result
import requests_oauthlib

RowsProxy = List[aiopg.sa.result.RowProxy]
ResultProxy = aiopg.sa.result.ResultProxy
OAuth2Session = requests_oauthlib.OAuth2Session
