

class IdbAccessor {
    constructor(server_url, db, username, password) {
        this.server_url = server_url
        this.db = db
        this.username = username
        this.password = password
        this.db_url = this.server_url + "/" + this.db

        this.auth = btoa(this.username + ":" + this.password)

    }
    
    do_query(prefix, data) {
        let headers = new Headers()
        headers.append('Authorization', "Basic " + this.auth)
        headers.append("Content-Type", "application/json");

        let query_url = this.db_url + '/' + prefix.join('/')
        const request = new Request(query_url,
            {
                headers: headers,
                method: "POST",
                body: JSON.stringify(data),
                credentials: "include"
            })

        return fetch(request);
    }

    head() {
        let headers = new Headers()
        headers.append('Authorization', "Basic " + this.auth)

        const request = new Request(this.db_url,
            {
                headers: headers,
                method: "HEAD",
                credentials: "include"
            });

        fetch(request).then((response) => console.log("head: " + response));
    }

}

/*
server = new IdbAccessor("https://infinitydb.com:37411/infinitydb/data", "ai/labels", "ai", "ai")
server.head()

server.do_query(["com.infinitydb.ai", "get_first_image_id"],
    data = {
        "image_set": "chlorella"
    }
)
*/

server = new IdbAccessor("https://localhost:37411/infinitydb/data", "boilerbay/genomics", "ai", "ai")
server.head()


server.do_query(["com.boilerbay.genomics", "get_sequence"], 
    data={
        "genome": "grch38",
        "chromosome": "chr1",
        "start": 1000000,
        "end": 1000100
    }
);