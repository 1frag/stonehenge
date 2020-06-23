let correct = new Set();
let type_ans = null;

function ok() {
    let ans = null;
    if (type_ans === 'ch') {
        if (correct.size === 0) {
            make('error', 'Choose at least one variant');
            return;
        }
        ans = Array.from(correct);
    } else {
        ans = $('#answer-plain-text')[0].value;
        if (ans.length() === 0) {
            make('error', 'Empty answer is not correct answer');
            return;
        }
    }
    $.ajax({
        url: '/tests/exam',
        method: 'POST',
        data: JSON.stringify({
            'answer': ans,
            'test_id': parseInt($('#test_id')[0].value),
        }),
    })
}

function add_ch(i, btn) {
    correct.add(i);
    $(btn).addClass('chosen-choice');
    btn.onclick = function () {
        correct.delete(i);
        $(btn).removeClass('chosen-choice');
        btn.onclick = () => add_ch(i, btn);
    };
}
