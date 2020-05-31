import sys
import asyncio
from sqlalchemy.sql.ddl import CreateTable, DropTable
from sqlalchemy.dialects.postgresql import CreateEnumType, DropEnumType
from stonehenge.users.tables import users, mission_enum
from stonehenge.migrations.env import f_engine
from typing import Optional
import aiopg.sa

engine = None  # type: Optional[aiopg.sa.Engine]


async def upgrade():
    async with engine.acquire() as conn:  # type: aiopg.sa.SAConnection
        await conn.execute(CreateEnumType(mission_enum))
        await conn.execute(CreateTable(users))


async def downgrade():
    async with engine.acquire() as conn:  # type: aiopg.sa.SAConnection
        await conn.execute(DropTable(users))
        await conn.execute(DropEnumType(mission_enum))


async def main():
    global engine
    engine = await f_engine
    if sys.argv[1].startswith('u'):
        print(f'Start upgrade {__file__}')
        await upgrade()
    elif sys.argv[1].startswith('d'):
        print(f'Start downgrade {__file__}')
        await downgrade()
    else:
        exit(1)
    print(f'Completed')

    engine.close()


if __name__ == '__main__':
    asyncio.run(main())
