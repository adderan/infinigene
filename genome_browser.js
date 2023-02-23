
class IdbAccessor {
    constructor(server_url, db, username, password) {
        this.server_url = server_url
        this.db = db
        this.username = username
        this.password = password
        this.db_url = this.server_url + "/" + this.db
        const headers = new Headers();
        headers.append('Authorization', "Basic " + self.username + " " + self.password);
        headers.append("Content-Type", "application/json");
        this.headers = headers;

    }
    
    do_query(prefix, data) {
        //const headers = new Headers();
        //headers.append('Authorization', "Basic " + self.username + " " + self.password);
        //headers.append("Content-Type", "application/json");
        let query_url = this.db_url + '/' + prefix.join('/')
        const request = new Request(query_url,
            {
                headers: this.headers,
                method: "POST",
                body: JSON.stringify(data)
            })

        return fetch(request);
    }

    head() {
        const request = new Request(this.db_url,
            {
                headers: this.headers,
                method: "HEAD",
            })
        fetch(request).then((response) => console.log("head: " + response));
    }

}


let server = new IdbAccessor(server_url="https://24.6.93.122:37411/infinitydb/data/", db="boilerbay/genomics", user="ai", password="ai")

server.head();

server.do_query(prefix=["Query2", "get_image_sets"], 
    data=null).then((image_sets) => console.log("image sets:" + image_sets));