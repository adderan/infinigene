const INTERFACE = "com.boilerbay.genomics"


var browser = null;
var server = null;

class SequenceElement {
    constructor(element_id, gene_set, genome, chromosome, start, end, strand) {
        this.element_id = element_id;
        this.gene_set = gene_set;
        this.genome = genome;
        this.chromosome = chromosome;
        this.start = start;
        this.end = end;
        this.strand = strand;

        this.track_height = 100;
    }
}

class RepeatElement extends SequenceElement {
    constructor(transcript_id, gene_set, genome, chromosome, start, end, strand, family) {
        super(transcript_id, gene_set, genome, chromosome, start, end, strand);
        this.family = family;

        this.line_width = 20;
    }

    draw(browser, draw_level) {
        let clickable_objects = [];
        let start = browser.to_screen_coordinates(this.start);

        let end = browser.to_screen_coordinates(this.end);

        start = Math.max(start, 0);
        end = Math.min(browser.canvas.width, end);
        ctx.fillStyle = "rgba(0.5, 0.5, 0, 0.8)";

        repeat_box = new Path2D();

        ctx.rect(start, draw_level - this.line_width/2, end-start, this.line_width);
        ctx.fill(repeat_box);

        clickable_objects.push({
            "path": repeat_box,
            "tooltip_info": [this.family]
        });

        ctx.fillStyle = "black";
        ctx.font = "20px sans bold";

        ctx.fillText(transcript_label, start+this.transcript_label_offset, draw_level - 20);
        return clickable_objects;
    }
}

class GeneElement extends SequenceElement {
    constructor(element_id, gene_set, genome, chromosome, start, end, strand, exons, gene_id) {
        super(element_id, gene_set, genome, chromosome, start, end, strand);
        this.exons = exons;
        this.gene_id = gene_id;

        this.color_codes = {
            "start_codon": "red",
            "CDS": "green",
            "5UTR": "yellow",
            "3UTR": "blue",
            "exon": "purple"
        };

        this.box_height = 50;
        this.line_width = 6;
        this.transcript_label_offset = 40;


    }
    draw(browser, draw_level) {

        let clickable_objects = [];
        let ctx = browser.canvas.getContext("2d");
        
        let start = browser.to_screen_coordinates(this.start);

        let end = browser.to_screen_coordinates(this.end);

        start = Math.max(start, 0);
        end = Math.min(browser.canvas.width, end);

        
        for ([exon_id, exon] of Object.entries(this.exons)) {

            let exon_start = browser.to_screen_coordinates(exon.start);
            let exon_end = browser.to_screen_coordinates(exon.end);

            exon_start = Math.max(0, exon_start);
            exon_end = Math.min(browser.canvas.width, exon_end);

            ctx.fillStyle = this.color_codes[exon.feature];
            const x0 = exon_start;
            const y0 = draw_level - this.box_height/2;
            const x1 = exon_end;
            const y1 = draw_level + this.box_height/2;

            const exon_box = new Path2D();
            exon_box.rect(x0, y0, x1-x0, y1-y0);
            ctx.fill(exon_box);

            clickable_objects.push({
                "path": exon_box,
                "tooltip_info": [exon.exon_id, exon.feature]
            });

        }
        //draw thin line for whole transcript
        ctx.fillStyle = "black";
        ctx.fillRect(start, draw_level - this.line_width/2, end-start, this.line_width);

        ctx.font = "20px Sans Bold";
        ctx.fillStyle = "black";
        let transcript_label = `${this.gene_id}`;
        ctx.fillText(transcript_label, start+this.transcript_label_offset, draw_level - 20);

        return clickable_objects;
    }   
}


class Browser {
    constructor(canvas) {
        /** @type {HTMLCanvasElement} */
        this.canvas = canvas;

        this.transcripts = {};
        this.position = 0;
        this.view_width = 10000;

        this.track_height = 50;
        this.line_width = 5;
        this.transcript_label_offset = 40;
        this.axis_y_offset = 6;
        this.axis_thickness = 2;
        this.axis_tick_height = 16;

        
        this.on_screen_objects = [];

        this.canvas.addEventListener('click', this);
        this.canvas.addEventListener('wheel', this);
        this.canvas.addEventListener('mouseup', this);
        this.canvas.addEventListener('mousedown', this);
        this.canvas.addEventListener('mouseleave', this);

        this.current_tooltip = null;

        this.active_gene_set_boxes = {};

        this.transcript_scope = 1.0; //distance in canvas widths to keep offscreen transcripts
    }

    handleEvent(event) {
        if (event.type == 'wheel') {
            if (event.deltaX == 0) return;
            browser.move(-1*event.deltaX);
            browser.refresh_canvas();
        }
        else if (event.type == "click") {
            this.current_tooltip = null;
            this.refresh_canvas();
            this.draw_tooltip(event.offsetX, event.offsetY);
        }
        else if (event.type == 'mousedown') {
            this.canvas.addEventListener('mousemove', this);
            this.dragPosition = event.pageX;
        }
        else if (event.type == 'mouseup') {
            this.canvas.removeEventListener('mousemove', this);

        }
        else if (event.type == 'mousemove') {
            let deltaX = event.pageX - this.dragPosition;
            if (deltaX == 0) return;
            this.move(deltaX);
            this.dragPosition = event.pageX;
            this.refresh_canvas();
        }
        else if (event.type == 'mouseleave') {
            this.canvas.removeEventListener('mousemove', this);
        }
        else {
            console.warn(`Unexpected event ${event.type}`);
        }
    }
    move(offset) {

        let scale = this.view_width/this.canvas.width;
        let new_position = this.position - parseInt(offset * scale);
        this.set_coordinates(this.genome, this.chromosome, new_position, this.view_width);

        if (Date.now() - this.last_track_refresh > 500) {
            this.update_tracks();
        }

        this.current_tooltip = null;
    }

    draw_tooltip(x, y) {
        const tooltip_info = this.get_object_at_position(x, y);
        if (tooltip_info == null) {
            return;
        }
        this.current_tooltip = (x, y);
        var ctx = this.canvas.getContext("2d");
        ctx.beginPath();
        let x_offset = 10;
        let y_offset = 10;
        if (x > this.canvas.width/2) {
            x_offset = -110;
        }
        if (y > this.canvas.height/2) {
            y_offset = -110;
        }
        const tooltip_x0 = x + x_offset;
        const tooltip_y0 = y + y_offset;
        //ctx.rect(tooltip_x0, tooltip_y0, 200, 100);

        ctx.fillStyle = "rgba(255, 212, 178, 0.9)";
        roundRect(ctx, tooltip_x0, tooltip_y0, 200, 100, 10);

        ctx.fillStyle = "black";
        ctx.font = "15px serif";

        let vpos = tooltip_y0 + 20;
        let xpos = tooltip_x0 + 20;
        for (let line of tooltip_info) {
            ctx.fillText(line, xpos, vpos);
            vpos += 20;
        }

    }

    get_selected_gene_sets() {
        let gene_set_selected = {};
        for (let box of Object.keys(this.active_gene_set_boxes)) {
            gene_set_selected[box] = this.active_gene_set_boxes[box].checked;
        }
        return gene_set_selected;
    }

    get_object_at_position(x, y) {
        const ctx = this.canvas.getContext("2d");
        for (const object of this.on_screen_objects) {
            if (ctx.isPointInPath(object.path, x, y)) {
                return object.tooltip_info;
            }

        }
        return null;
    }

    draw_axis() {
        let ctx = this.canvas.getContext("2d");
        ctx.fillRect(
            0, 
            this.axis_y_offset - this.axis_thickness, 
            this.canvas.width,
            this.axis_thickness);

        this.draw_axis_tick(this.canvas.width/4);
        this.draw_axis_tick(this.canvas.width/2);
        this.draw_axis_tick(this.canvas.width*0.75);
        this.draw_axis_tick(0);
        this.draw_axis_tick(this.canvas.width);
        
    }

    draw_axis_tick(x) {
        let x0 = this.from_screen_coordinates(x);
        let ctx = this.canvas.getContext("2d");
        ctx.fillRect(
            x, 
            this.axis_y_offset - this.axis_tick_height/2, 
            this.axis_thickness, 
            this.axis_tick_height);


        let units = "bp";
        if (x0 > 1e6) {
            x0 = x0/1e6;
            units = "Mb";
        }
        else if (x0 > 1e3) {
            x0 = x0/1e3;
            units = "Kb";
        }
        let label = `${x0} ${units}`;

        ctx.font = "15px sans bold";
        let label_x_pos = Math.max(0, x-20); //prevent label going off left edge
        label_x_pos = Math.min(label_x_pos, this.canvas.width-50); //prevent label going off right edge
        ctx.fillText(label, label_x_pos, this.axis_y_offset + this.axis_tick_height+4);

    }


    from_screen_coordinates(x) {
        let scale = this.view_width / this.canvas.width;
        return (x - this.canvas.width/2) * scale + this.position;
    }

    to_screen_coordinates(x0) {
        let scale = this.view_width / this.canvas.width;
        return this.canvas.width/2.0 + (x0 - this.position)/scale;
    }

    set_coordinates(genome, chromosome, position, view_width) {
        this.genome = genome;
        this.chromosome = chromosome;
        this.position = position;
        this.view_width = view_width;
    }

    async update_tracks() {
        console.log("Updating tracks from server.")
        let transcript_ids = await get_transcripts_in_range(
                this.genome, 
                this.chromosome, 
                this.position, 
                this.position + this.view_width
        );
        if (transcript_ids == null) return;


        for (let transcript_id of transcript_ids) {
            if (transcript_id in this.transcripts) {
                console.log("Skipping downloading transcript");
                continue;
            }
            let transcript = await get_transcript(server, transcript_id);
            this.transcripts[transcript_id] = transcript;
            this.refresh_canvas();
        }
        this.last_track_refresh = Date.now();
    }

    refresh_canvas() {
        
        let ctx = this.canvas.getContext("2d");
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.get_selected_gene_sets();

        this.on_screen_objects = [];
        let level = 100;

        this.canvas.width = window.innerWidth;


        //Drop out-of-view transcripts and resize canvas in advance, because resizing it will clear
        //it.
        let transcripts_to_draw = [];
        for (let transcript_id of Object.keys(this.transcripts)) {
            let transcript = this.transcripts[transcript_id];
            if (!transcript) {
                delete this.transcripts[transcript_id];
                continue
            }

            let transcript_screen_end = this.to_screen_coordinates(transcript.end);
            let transcript_screen_start = this.to_screen_coordinates(transcript.start);

            let far_before = transcript_screen_end < -1*this.transcript_scope*this.canvas_width;
            let far_after = transcript_screen_start > this.transcript_scope*this.canvas_width;
            if (far_before || far_after) {
                console.log("Deleting far out-of-scope transcript");
                delete this.transcripts[transcript_id];
            }

            if ((transcript_screen_end < 0) || (transcript_screen_start > this.canvas.width)) {
                continue;
            }
            transcripts_to_draw.push(transcript);
        }
        this.canvas.height = 100 * transcripts_to_draw.length + 100;

        this.draw_axis();

        let gene_set_selected = this.get_selected_gene_sets();

        for (let transcript of transcripts_to_draw) {
            if (!gene_set_selected[transcript.gene_set]) continue;
            let clickable_objects = transcript.draw(this, level);
            this.on_screen_objects = this.on_screen_objects.concat(clickable_objects);
            level += 100;
        }
        if (this.current_tooltip != null) {
            this.draw_tooltip(this.current_tooltip[0], this.current_tooltip[1]);
        }
    }
    

}


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

get_transcripts_in_gene = async function(server, gene) {
    let response = await server.do_query(
            [INTERFACE, "get_transcripts_in_gene"], 
            {"gene": gene}
    );
    if (response == null) return null;
    response = await response.json();
    let transcript_ids = Object.keys(response);
    return transcript_ids;
}

get_transcript = async function(server, transcript_id) {
    let response = await server.do_query(
        [INTERFACE, "get_transcript"],
        {"transcript_id": transcript_id}
    );

    if (response == null || response.status != 200) return null;
    response = await response.json();

    let gene_set = response["_gene_set"];
    let genome = response["_genome"];
    let chromosome = response["_chromosome"];
    let start = parseInt(response["_start"].slice(1));
    let end = parseInt(response["_end"].slice(1));
    let strand = response["_strand"];

    let seq_element = null;
    console.log(response["_type"]);

    if (response["_type"] == "repeat") {
        let family = response["_family"];

        seq_element = new RepeatElement(
            transcript_id,
            gene_set,
            genome,
            chromosome,
            start, 
            end,
            strand,
            family
        );

    }
    else {
        gene_id = response["_gene"];
        exons = {};
        for ([exon_id, exon] of Object.entries(response["_exons"])) {
            exon = flatten_to_list(exon);
            exons[exon_id] = {
                exon_id: exon_id,
                chromosome: exon[0],
                start: parseInt(exon[1]),
                end: parseInt(exon[2]),
                strand: exon[3],
                feature: exon[4]
            }
        }

        seq_element = new GeneElement(
            transcript_id,
            gene_set,
            genome,
            chromosome,
            start,
            end,
            strand,
            exons,
            gene_id
        );
    }
    
    return seq_element;
}

get_transcripts_in_range = async function(genome, chromosome, start, end) {
    let response = await server.do_query([INTERFACE, "get_transcripts_in_range"],
        data = {
            "genome": genome,
            "chromosome": chromosome,
            "start": start, 
            "end": end
        }
    );

    if (response == null || response.status != 200) {
        return null;
    }
    response = await response.json();
    console.log(response);
    for (let transcript_prefix of Object.keys(response)) {
        let transcript_suffix = response[transcript_prefix];
        if (transcript_suffix == null) continue;
        console.log(flatten_to_list(transcript_suffix));
        
    }
    transcript_ids = Object.keys(response);
    return transcript_ids;
    
}


go_to_position = async function() {
    if (server == null) {
        set_disconnected_status();
        return;
    }
    let coordinates_field = document.getElementById("coordinates");
    const coords_exp = /^([a-zA-Z0-9]+):([a-zA-Z0-9]+):([0-9]+)$/;
    const coords = coordinates_field.value.match(coords_exp)
    let genome, chromosome, position;
    if (coords) {
        genome = coords[1];
        chromosome = coords[2];
        position = parseInt(coords[3]);
    }

    if (genome == null) {
        let transcript = await get_transcript(server, coordinates_field.value);
        if (transcript) {
            genome = transcript.genome;
            chromosome = transcript.chromosome;
            position = parseInt(transcript.start);
        }
    }
    if (genome == null) {
        //try to find the gene name
        let transcripts_in_gene = await get_transcripts_in_gene(server, coordinates_field.value);
        if (transcripts_in_gene) {
            transcript = await get_transcript(server, transcripts_in_gene[0]);
            genome = transcript.genome;
            chromosome = transcript.chromosome;
            position = parseInt(transcript.start);
            
        }

    }
    if (genome == null) {
        alert("Invalid coordinates or gene name.");
        return;
    }


    let view_width_field = document.getElementById("view_width");
    view_width = parseInt(view_width_field.value);
    
    browser.set_coordinates(
        genome, 
        chromosome, 
        position, 
        view_width);
    browser.update_tracks();
    browser.refresh_canvas();

}

function zoom_out() {
    browser.view_width *= 2;
    browser.refresh_canvas();
}
function zoom_in() {
    browser.view_width /= 2;
    browser.refresh_canvas();
}

function refresh_button() {
    browser.update_tracks();
    browser.refresh_canvas();
}

window.onload = function() {
    if (sessionStorage.getItem('username') != null) {
        server = new IdbAccessor(sessionStorage.getItem('server_url'), 'boilerbay/genomics', sessionStorage.getItem('username'), sessionStorage.getItem('password'));
    }
    set_login_status();

    /** @type {HTMLCanvasElement} */
    var canvas = document.getElementById("canvas")

    browser = new Browser(canvas);
    browser.refresh_canvas();

    let gene_sets = ['Ensembl', 'refGene'];
    let gene_sets_div = document.getElementById('gene_sets');
    browser.active_gene_set_boxes = {};
    for (let gene_set of gene_sets) {
        let gene_set_div = document.createElement('div');
        gene_set_div.style = 'display:inline; margin:10px;';
        let box = document.createElement('input');
        box.id = `${gene_set}_box`;
        box.setAttribute('type', 'checkbox');
        box_label = document.createElement('label');
        box_label.htmlFor = `${gene_set}_box`;
        box_label.innerHTML = gene_set;
        box_label.style = "padding:8px;"
        box.checked = true;
        box.addEventListener('click', () => browser.refresh_canvas());
        gene_set_div.append(box_label);
        gene_set_div.append(box);
        gene_sets_div.append(gene_set_div);

        browser.active_gene_set_boxes[gene_set] = box;
    }

}


//Window Listeners

window.onresize = function() {
    browser.refresh_canvas();
}


function roundRect(context, x, y, w, h, radius) {
    var r = x + w;
    var b = y + h;
    context.beginPath();
    context.strokeStyle="green";
    context.lineWidth="4";
    context.moveTo(x+radius, y);
    context.lineTo(r-radius, y);
    context.quadraticCurveTo(r, y, r, y+radius);
    context.lineTo(r, y+h-radius);
    context.quadraticCurveTo(r, b, r-radius, b);
    context.lineTo(x+radius, b);
    context.quadraticCurveTo(x, b, x, b-radius);
    context.lineTo(x, y+radius);
    context.quadraticCurveTo(x, y, x+radius, y);
    context.fill();
}