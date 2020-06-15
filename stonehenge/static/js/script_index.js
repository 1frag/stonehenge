let inc = null;
let state = null;
$(window).load(function () {
    inc = document.getElementById('inc');
});

function tests() {
    /*
    <div class="message my-btn maybe-chosen" style="margin-left: 22%; width: 25%; display: inline-block">
        Watch previews tests
    </div>
    <div class="message my-btn maybe-chosen" style="width: 25%; display: inline-block">
        Create new test
    </div>
    <hr noshade>
    */
    if (state === 'tests') return; else state = 'tests'; let d1 = document.createElement('div'); d1.className = 'message my-btn maybe-chosen'; d1.style['margin-left'] = '22%'; d1.style['width'] = '25%'; d1.style['display'] = 'inline-block'; d1.innerText = 'Watch previews tests'; d1.onclick = function () {d1.style['background-color'] = '#00936344'; d1.className = d2.className = 'message my-btn'; return watchPreviewsTests();}; let d2 = document.createElement('div'); d2.className = 'message my-btn maybe-chosen'; d2.style['width'] = '25%'; d2.style['display'] = 'inline-block'; d2.innerText = 'Create new test'; d2.onclick = function () { d2.style['background-color'] = '#00936344'; d1.className = d2.className = 'message my-btn'; return createNewTest(); }; let hr = document.createElement('hr'); inc.insertBefore(d1, null); inc.insertBefore(d2, null); inc.insertBefore(hr, null);
}

function watchPreviewsTests() {
    if (state === 'watchPreviewsTests') return;
    else state = 'watchPreviewsTests';
}

function createNewTest() {
    /*
    <p>Set the question:</p>
    <textarea style="width: 90%" rows=4></textarea>
    <div class="float-left">
        <p style="display: inline-block">Append file:</p>
        <input type="file" class="btn">
    </div><br/>
    <input type="button" class="btn float-right"
           style="margin-right: 10%" value="Next to answer">
    <br><br><hr noshade>
    */
    if (state === 'createNewTest') return; else state = 'createNewTest'; let p1 = document.createElement('p'); p1.innerText = 'Set the question:'; let txtar = document.createElement('textarea'); txtar.style['width'] = '90%'; txtar.rows = 4; let d1 = document.createElement('div'); d1.className = 'float-left'; let p2 = document.createElement('p'); p2.style['display'] = 'inline-block'; p2.innerText = 'Append file:'; let i1 = document.createElement('input'); i1.type = 'file'; i1.className = 'btn'; d1.insertBefore(p2, null); d1.insertBefore(i1, null); let i2 = document.createElement('input'); i2.type = 'button'; i2.className = 'btn float-right'; i2.style['margin-right'] = '10%'; i2.value = 'Next to answer'; let hr = document.createElement('hr'); hr.className = 'hr'; inc.insertBefore(p1, null); inc.insertBefore(txtar, null); inc.insertBefore(d1, null); inc.insertBefore(document.createElement('br'), null); inc.insertBefore(i2, null); inc.insertBefore(document.createElement('br'), null); inc.insertBefore(document.createElement('br'), null); inc.insertBefore(hr, null);
}