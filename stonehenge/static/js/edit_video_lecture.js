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

function sendDeleteVideo() {
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