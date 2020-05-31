from typing import List
import aiopg.sa.result

RowsProxy = List[aiopg.sa.result.RowProxy]
ResultProxy = aiopg.sa.result.ResultProxy
