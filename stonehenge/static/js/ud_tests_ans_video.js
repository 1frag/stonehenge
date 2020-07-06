// this file contains crUD for tests and video lectures

function sendEditInfo() {
    let formData = new FormData(document.forms['edit-form']);
    $.ajax({
        url: '/video/edit',
        method: 'POST',
        data: formData,
        success: (r) => {
            location.reload();
        },
        error: (r) => {
            make('error', r.statusText, 'Ошибка изменения');
            $('#close-btn').click()
        },
        processData: false,
        contentType: false,
    })
}

function sendDeleteVideo() { // used by modal_for_delete
    $.ajax({
        url: '/video/remove',
        method: 'POST', // I am afraid to use DELETE method due to ajax specific
        data: JSON.stringify({v_id: $('#video-id').val()}),
        success: (r) => {
            document.location.href = '/'
        },
        error: (r) => {
            make('error', r.statusText, 'Ошибка удаления');
            $('#close-btn-del').click()
        },
        processData: false,
        contentType: false,
    })
}

function sendTestDelete() { // used by modal_for_delete
    $.ajax({
        url: '/tests/remove',
        method: 'POST',
        data: JSON.stringify({t_id: $('#test-id').val()}),
        success: (r) => {
            document.location.href = '/'
        },
        error: (r) => {
            make('error', r.statusText, 'Ошибка удаления');
            $('#close-btn-del').click()
        },
        processData: false,
        contentType: false,
    });
}
