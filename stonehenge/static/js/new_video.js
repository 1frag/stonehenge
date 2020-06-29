async function ok_btn() {
    let formData = new FormData(document.forms['new-video-form']);
    let file_name = null; let tr = null;

    await fetch('/video/new', {
        method: 'POST',
    }).then(async function (r) {
        let b = await r.text();
        if (r.status === 201) {
            file_name = b;
        } else tr = b;
        console.log('in then');
    });
    if (file_name === null) {
        return make('error', tr, 'Ошибка');
    }

    console.log('b4 upload_big_file');
    await upload_big_file(
        '#video_file',
        '/video/upload',
        file_name,
    );

    console.log('b4 latest fetch');
    await fetch('/video/updated', {
        body: JSON.stringify({
            'levels': formData.getAll('levels'),
            'title': formData.get('title'),
            'description': formData.get('description'),
            'video_file': file_name,
        }),
        method: 'POST',
    }).then(async function (r) {
        return;
        document.location.href = '/video/' + await r.text();
    });
}