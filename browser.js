var server = null;
var browser = null;
const INTERFACE = "com.boilerbay.genomics"
class Browser {
    constructor(canvas) {
        this.canvas = canvas;
        this.transcripts = {};
        this.position = 0;
        this.view_width = 10000;

        this.track_height = 50;
        this.line_width = 5;
        this.transcript_label_offset = 40;
        this.axis_y_offset = 6;
        this.axis_thickness = 2;
        this.axis_tick_height = 12;

        this.color_codes = {
            "start_codon": "red",
            "CDS": "green",
            "5UTR": "yellow",
            "3UTR": "blue",
            "exon": "purple"
        };
        let ctx = this.canvas.getContext("2d");

    }
    move(offset) {

        let scale = this.view_width/this.canvas.width;
        let new_position = this.position - parseInt(offset * scale);
        this.set_coordinates(this.genome, this.chromosome, new_position, this.view_width);
        
    }

    draw_axis() {
        let ctx = this.canvas.getContext("2d");
        ctx.fillRect(
            0, 
            this.axis_y_offset - this.axis_thickness, 
            this.canvas.width,
            this.axis_thickness);

        ctx.fillRect(
            this.canvas.width/2, 
            this.axis_y_offset - this.axis_tick_height/2, 
            this.axis_thickness, 
            this.axis_tick_height);

        ctx.font = "12px sans bold";
        ctx.fillText()

    }

    to_screen_coordinates(x0) {
        let scale = this.view_width / this.canvas.width;
        return (x0 - this.position)/scale;
    }

    set_coordinates(genome, chromosome, position, view_width) {
        this.genome = genome;
        this.chromosome = chromosome;
        this.position = position;
        this.view_width = view_width;
    }

    async update_tracks(transcript_ids) {
        transcript_ids = await get_transcripts_in_range(
                this.genome, 
                this.chromosome, 
                this.position, 
                this.position + this.view_width
        );

        for (let transcript_id of transcript_ids) {
            if (transcript_id in this.transcripts) {
                continue;
            }
            transcript = await get_transcript(server, transcript_id);
            this.transcripts[transcript_id] = transcript;
            this.refresh_canvas();
        }
    }

    draw_transcript(transcript_id, draw_level) {
        let ctx = this.canvas.getContext("2d");
        let scale = this.view_width/this.canvas.width
        let transcript = this.transcripts[transcript_id];
        
        let start = this.to_screen_coordinates(transcript.start);

        let end = this.to_screen_coordinates(transcript.end);

        start = Math.max(start, 0);
        end = Math.min(this.canvas.width, end);

        
        for ([exon_id, exon] of Object.entries(transcript.exons)) {

            let exon_start = this.to_screen_coordinates(exon.start);
            let exon_end = this.to_screen_coordinates(exon.end);

            exon_start = Math.max(0, exon_start);
            exon_end = Math.min(this.canvas.width, exon_end);

            ctx.fillStyle = this.color_codes[exon.feature];
            ctx.fillRect(exon_start, draw_level - this.track_height/2, exon_end-exon_start, this.track_height);

        }
        //draw thin line for whole transcript
        ctx.fillStyle = "black";
        ctx.fillRect(start, draw_level - this.line_width/2, end-start, this.line_width);

        ctx.font = "20px Sans Bold";
        ctx.fillStyle = "black";
        ctx.fillText(transcript_id, start+this.transcript_label_offset, draw_level - 20);

    }

    refresh_canvas() {
        let ctx = this.canvas.getContext("2d");
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        let level = 100;

        this.canvas.width = window.innerWidth;

        console.log(this.transcripts);

        //Drop out-of-view transcripts and resize canvas in advance, because resizing it will clear
        //it.
        for (let transcript_id of Object.keys(this.transcripts)) {
            let transcript = this.transcripts[transcript_id];
            if ((transcript.end < this.position) || (transcript.start > this.position + this.view_width)) {
                delete this.transcripts[transcript_id];
                continue;
            }
        }
        this.canvas.height = 100 * Object.keys(this.transcripts).length + 100;

        this.draw_axis();

        for (let transcript_id of Object.keys(this.transcripts)) {
            this.draw_transcript(transcript_id, level)
            level += 100;
        }
    }

}

class Track {

};

class GeneTrack extends Track {
    constructor(gene_name, start, end) {
        this.gene_name = gene_name;
        this.start = start;
        this.end = end;
    }

    draw(canvas, position, height) {
        let ctx = canvas.getContext("2d");
        ctx.fillRect(0, position, canvas.width, position+height);

    }
};

class SequenceTrack extends Track {

};

var browser = null;

connect_server = async function() {
    let server_field = document.getElementById("server_url");
    let user_field = document.getElementById("username");
    let password_field = document.getElementById("password");
    let connection_status = document.getElementById("connection_status");

    server_url = `${server_field.value}:37411/infinitydb/data`
    server = new IdbAccessor(server_url, "boilerbay/genomics", user_field.value, password_field.value)

    
    sessionStorage.setItem('server_url', server_url);
    sessionStorage.setItem('username', user_field.value);
    sessionStorage.setItem('password', password_field.value);
    

    let login_pane = document.getElementById("loginpane")
    login_pane.style.display = "none";

    set_login_status();

}

set_login_status = async function() {
    let connection_status = document.getElementById("connection_status");
    let login_button = document.getElementById("login");
    let server_status = 0;
    if (server) {
        response = await server.head();
        server_status = response.status;

    }

    if (server_status == 200) {
        connection_status.innerHTML = `Connected to ${server.server_url}`;
        login_button.onclick = logout_server;
        login_button.innerHTML = 'Logout';
    }
    else {
        if (server) {
            //server exists but couldn't connect
            connection_status.innerHTML = `Login failed with status ${server_status}`;
        }
        connection_status.innerHTML = "Not logged in.";
        login_button.onclick = show_loginpane;
        login_button.innerHTML = "Login";
    }

}


window.onload = function() {

}

show_loginpane = function() {
    document.getElementById('loginpane').style.display='block';
}
hide_loginpane = function() {
    document.getElementById('loginpane').style.display='none';
}

logout_server = function() {
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('password');
    sessionStorage.removeItem('server_url');
    server = null;
    let connection_status = document.getElementById("connection_status");
    connection_status.innerHTML = "Not logged in.";

    let login_button = document.getElementById("login");
    login_button.onclick = show_loginpane;
    login_button.innerHTML = "Login";
}

set_disconnected_status = function() {
    document.getElementById("connection_status").innerHTML = "Must login first."
}

get_transcript = async function(server, transcript_id) {
    response = await server.do_query([INTERFACE, "get_transcript"],
        data = {"transcript_id": transcript_id

        }
    )
    response = await response.json();

    exons = {};
    for ([exon_id, exon] of Object.entries(response["_exons"])) {
        exon = flatten_to_list(exon);
        exons[exon_id] = {
            chromosome: exon[0],
            start: parseInt(exon[1]),
            end: parseInt(exon[2]),
            strand: exon[3],
            feature: exon[4]
        }
    }

    transcript = {
        chromosome: response["_chromosome"],
        start: parseInt(response["_start"].slice(1)),
        end: parseInt(response["_end"].slice(1)),
        exons: exons
    };
    
    return transcript;
}

get_transcripts_in_range = async function(genome, chromosome, start, end) {
    response = await server.do_query([INTERFACE, "get_transcripts_in_range"],
        data = {
            "genome": genome,
            "chromosome": chromosome,
            "start": start, 
            "end": end
        }
    );
    response = await response.json();
    transcript_ids = Object.keys(response);
    return transcript_ids;
    
}

go_to_position = async function() {
    if (server == null) {
        set_disconnected_status();
        return;
    }
    const display_length = 20;
    let coordinates_field = document.getElementById("coordinates");
    const coords_exp = /^([a-zA-Z0-9]+):([a-zA-Z0-9]+):([0-9]+)$/;
    const coords = coordinates_field.value.match(coords_exp)
    if (coords == null) {
        alert("Invalid coordinates");
        return;
    }
    genome = coords[1];
    chromosome = coords[2];
    position = parseInt(coords[3]);

    response = await server.do_query([INTERFACE, "get_sequence"], 
        data={
            "genome": "grch38",
            "chromosome": chromosome,
            "start": position - display_length,
            "end": position + display_length
        }
    );
    let seq = await response.json();
    seq = seq.join(" ");


    let view_width_field = document.getElementById("view_width");
    view_width = parseInt(view_width_field.value);
    console.log(view_width);
    
    browser.set_coordinates(
        genome, 
        chromosome, 
        position, 
        view_width);
    browser.update_tracks();
    browser.refresh_canvas();

}

function dragCanvas(event) {
    browser.move(event.pageX - cur_drag_pos);
    browser.refresh_canvas();
    cur_drag_pos = event.pageX;

}

var cur_drag_pos = 0;
canvas.onmousedown = function(event) {
    cur_drag_pos = event.pageX;
    canvas.addEventListener('mousemove', dragCanvas);
}
canvas.onmouseup = function(event) {
    canvas.removeEventListener('mousemove', dragCanvas);
    browser.update_tracks();
    browser.refresh_canvas();

}

window.onresize = function() {
    browser.refresh_canvas();
}

if (sessionStorage.getItem('username') != null) {
    server = new IdbAccessor(sessionStorage.getItem('server_url'), 'boilerbay/genomics', sessionStorage.getItem('username'), sessionStorage.getItem('password'));
}
set_login_status();
canvas = document.getElementById("canvas")
browser = new Browser(canvas);
