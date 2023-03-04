

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
        let escaped_data = {};
        for (let key in data) {
            let escaped_key = "_" + key;
            escaped_data[escaped_key] = data[key];
        }

        prefix = prefix.map(x => `\"${x}\"`)
        prefix = prefix.map(encodeURIComponent).join("/");

        let query_url = new URL(this.db_url + '/' + prefix);
        query_url.searchParams.append("action", "execute-query");

        const request = new Request(query_url,
            {
                headers: {
                    "Authorization": "Basic " + this.auth,
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify(escaped_data),
            })
        

        return fetch(request);
    }

    head() {
        const request = new Request(this.db_url,
            {
                headers: {
                    "Authorization": "Basic " + this.auth
                },
                method: "HEAD"
            });

        fetch(request).then((response) => console.log("head: " + response));
    }

}

server = new IdbAccessor("https://localhost:37411/infinitydb/data", "boilerbay/genomics", "ai", "ai")
server.head()


response = server.do_query(["com.boilerbay.genomics", "get_sequence"], 
    data={
        "genome": "grch38",
        "chromosome": "chr1",
        "start": 1000000,
        "end": 1000100
    }
).then(response => response.text()).then(response => console.log(response))