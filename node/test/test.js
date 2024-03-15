let a = "hello"; // init
let b = "world";

let not_used = "https://google.com/";

// Much advanced
console.log(a + " " + b);


let domain = "typicode.com";
let subdomain = "jsonplaceholder";
let path = "posts";
let full_domain = subdomain + "." + domain;
let schema = "https://" + full_domain;
let url = schema + "/" + path;

let test = 1;

if (test == 0) {
    url = "https://chalmers.se/";
}

if (test == 1) {
    let testScope = "https://kth.se/";
    fetch(url)
    .then(response => response.json())
    .then(data => {
        for (let i = 0; i < data.length; i++) {
            console.log(data[i].title);
            // prepend to body
            let innerScope = document.createElement("p");
            innerScope.innerHTML = data[i].title;
            document.body.prepend(innerScope);
        }
      })
      .catch(error => console.error(error));
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