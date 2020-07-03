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
            make('error', r.statusText, 'Ошибка');
            $('#close-btn').click()
        },
        processData: false,
        contentType: false,
    })
}