const canvas = document.getElementById("canvas");

const ctx = canvas.getContext("2d");
ctx.fillStyle = "green";

ctx.fillRect(10, 10, 150, 150);

let seq_url = `${SCRIPT_ROOT}/sequence/grch38/chr1/1000000/1000100`;

//let seq = fetch(seq_url).then(response => response.text()).then(response => document.write(response));

go_button = document.getElementById("go");

function display_sequence() {
    fetch(seq_url).then(response => response.text()).then(response => alert(response));
};
go_button.onclick = display_sequence;

