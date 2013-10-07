var ind = document.URL.indexOf("?");
var str = document.URL.substring(ind);
console.log(str);
if (str == "?prompt=success"){
    setTimeout(function() {
    document.location = "/login.html"; } , 2000);
    
}
