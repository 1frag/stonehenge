function ok_btn() {
    let formData = new FormData(document.forms['new-video-form']);
    $.ajax({
        url: '/video/new',
        method: 'POST',
        data: formData,
        success: function (data, status, response) {
            document.location.href = '/video/' + data;
        },
        error: function (response) {
            make('error', response.statusText)
        },
        processData: false,
        contentType: false,
    })
}