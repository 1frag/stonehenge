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
    print(t.validate(data))
    assert t.validate(data) == (
        {'type_answer': 'pt', 'correct': 'asd',
         'case_ins': True, 'choice': None,
         'question_txt': 'qwe', 'question_bytes': b'',
         'levels': ['A1', 'A2']
         }, None
    )
