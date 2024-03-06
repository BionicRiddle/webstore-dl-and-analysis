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

let test = 1;

if (test == 0) {
    url = "https://chalmers.se/";
}

switch (test) {
    case 0:
        url = "https://gp.se/";
        break;
    case 1:
        url = "https://google.se/";
        break;
    default:
        url = "https://kth.se/";
        break;
}

if (test == 1) {
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
}
