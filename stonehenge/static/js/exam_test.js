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
        let v = $('#answer-plain-text')
        ans = v.val();
        if (ans.length === 0) {
            make('error', 'Empty answer is not correct answer');
            return;
        }
        v[0].disabled = true;
    }
    $.ajax({
        url: '/tests/exam',
        method: 'POST',
        data: JSON.stringify({
            'answer': ans,
            'test_id': parseInt($('#test_id')[0].value),
        }),
        success: function (data) {
            if (type_ans === 'ch') {
                ['correct', 'incorrect'].forEach(n => {
                    data.report[n].forEach(e => {
                        $('#ch-btn-' + e).addClass(n);
                    })
                });
            } else {
                $('#answer-plain-text').addClass(
                    data.report ? 'correct' : 'incorrect'
                );
            }
            $('#mark-block')[0].style.display = 'block';
            $('#how-many-give')[0].innerText = data.mark;
            let ok = $('#ok-btn');
            ok[0].onclick = next;
            ok.val('Дальше');
        }
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

function next() {
    window.location.reload();
}
