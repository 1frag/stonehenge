from stonehenge.controllers import TestController
from multidict import MultiDict


async def test_validate_form_create_new_test():
    data = MultiDict([
        ('question_txt', 'qwe'),
        ('al', 'plain-text'),
        ('case-ins', 'on'),
        ('cor-answer', 'asd'),
        ('levels', 'A1'),
        ('levels', 'A2'),
    ])
    t = TestController()
    assert t.validate(data) == (
        ({'txt': 'qwe', 'bytes': b''},
         {'type': 'pt', 'correct': 'asd', 'case-ins': True},
         ['A1', 'A2']),
        None
    )
