/**Solution based on
 * https://deliciousbrains.com/using-javascript-file-api-to-avoid-file-upload-limits/
 * Thanks to @mattgrshaw
 * */

async function upload_big_file(target, url) {
    let reader = {};
    let file = {};
    const slice_size = 8 * 1024 * 16;
    let first_time = true;

    reader = new FileReader();
    file = document.querySelector(target).files[0];
    upload_file(0);

    function upload_file(start) {
        const next_slice = start + slice_size + 1;
        const blob = file.slice(start, next_slice);

        reader.onloadend = function (event) {
            if (event.target.readyState !== FileReader.DONE) {
                return;
            }
            console.log('data = ' + JSON.stringify({
                file_data: event.target.result,
                file: file.name,
                file_type: file.type,
            }) + '\nstart=' + start)

            $.ajax({
                url: url,
                type: 'POST',
                dataType: 'json',
                cache: false,
                async: true,
                data: JSON.stringify({
                    file_data: event.target.result,
                    file: file.name,
                    file_type: file.type,
                    first_time: first_time,
                }),
                statusCode: {
                    202: function (data) {
                        first_time = false;
                        const size_done = start + slice_size;
                        const percent_done = Math.floor(
                            (size_done / file.size) * 100
                        );

                        if (next_slice < file.size) {
                            // Update upload progress
                            $('#dbi-upload-progress').html(
                                `Uploading File -  ${percent_done}%`
                            );

                            // More to upload, call function recursively
                            upload_file(next_slice);
                        } else {
                            // Update upload progress
                            $('#dbi-upload-progress').html(
                                'Upload Complete!'
                            );
                        }
                    }
                },
            });
        };

        reader.readAsDataURL(blob);
    }
}
