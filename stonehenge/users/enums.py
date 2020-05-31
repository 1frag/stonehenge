from enum import Enum, unique


@unique
class UserMission(Enum):
    student = 'student'
    teacher = 'teacher'
    advertiser = 'advertiser'
