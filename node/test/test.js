let a = "hello"; // init
let b = "world";

let not_used = "https://google.com/";

// Much advanced
console.log(a + " " + b);

let schema = "https://";
let domain = "typicode.com";
let subdomain = "jsonplaceholder";
let path = "posts";
let url = schema + subdomain + "." + domain + "/" + path;

fetch(url)
.then(response => response.json())
.then(data => {
    for (let i = 0; i < data.length; i++) {
        console.log(data[i].title);
        // prepend to body
        let p = document.createElement("p");
        p.innerHTML = data[i].title;
        document.body.prepend(p);
    }
  })
  .catch(error => console.error(error));