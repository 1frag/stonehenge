function saveProfile() {
    $.ajax({
        url: '/profile',
        method: 'POST',
        data: JSON.stringify({
            'new_level': $('#level').val(),
        }),
        success: function () {
            make('success', '', 'Сохранено');
        }
    })
}