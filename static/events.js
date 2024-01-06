window.addEventListener("DOMContentLoaded", function(event){
    $('#foam').css('visibility', 'hidden');
});

var shw = 0;
function show() {
    if (shw == 0){
        $('#foam').css('visibility', 'visible');
        shw = 1;
    }
    else {
        $('#foam').css('visibility', 'hidden');
        shw = 0;
    }
}

function hasSpace() {
    let name = document.getElementById("eventName").value;
    if (/\s/g.test(name)) {
        alert('name cannot contain spaces!');
    }
}