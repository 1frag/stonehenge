$(function () {
    $('#answer-kind').change(function () {
        ['ca', 'pt'].map(e => $('#b' + e)[0].style.display =
            $('#r' + e)[0].checked ? 'block' : 'none');
    });
});

let cur = 1;
$(document).ready(function () {
    /*After click to plus -> add new row*/
    let plus = $('#ca-plus-ans')[0]
    plus.onclick = function () {
        $('#table-with-answers tr:last').after(
            '<tr id="row' + cur + '">\n' +
            '    <td><input type="text" style="width: 90%;" name="a' + cur + '"></td>\n' +
            '    <td><input type="checkbox" name="b' + cur + '" class="custom-checkbox"></td>\n' +
            '    <td><button class="btn-danger" name="c' + cur + '">remove</button></td>\n' +
            '</tr>'
        );
        let c = cur;
        $('[name=c' + cur + ']')[0].onclick = _ => $('#row' + c).remove();
        cur += 1;
    };
    [1, 2, 3].map(_ => plus.onclick());
    /* end */
});

/* after submit views form */
function createSubmit() {
    let formData = new FormData(document.forms['creating-form']);
    $.ajax({
        url: '/tests/new',
        data: formData,
        method: 'POST',
        success: function (data, status, response) {
            document.location.href = '/tests/' + data;
        },
        error: function (response) {
            make('error', response.statusText)
        },
        processData: false,
        contentType: false,
    });
    return false;
}

/* end */
