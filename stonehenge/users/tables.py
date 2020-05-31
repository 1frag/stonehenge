import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from stonehenge.migrations import metadata
from stonehenge.users.enums import UserMission


__all__ = ['users', 'mission_enum', ]


mission_enum = postgresql.ENUM(UserMission)


users = sa.Table(
    'users', metadata,
    sa.Column('id', sa.Integer, primary_key=True, index=True),
    sa.Column('username', sa.String(200), unique=True, nullable=False),
    sa.Column('email', sa.String(200), unique=True, nullable=False),
    sa.Column('password', sa.String(10), nullable=False),
    sa.Column('avatar_url', sa.Text),
    sa.Column('mission', mission_enum),
)
