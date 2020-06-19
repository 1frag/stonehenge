function signOut() {
    $.ajax({
        url: '/sign_out',
        method: 'POST',
        success: function () {
            console.log('success');
            document.location.href = '/';
        },
        error: function () {
            console.log('error');
            document.location.href = '/';
        },
    });
}