//Execute Code in a post

$( document ).ready(function() {
    $('.execute_link').click(function ()
{
    var tag = $($(this).parents(".code_sample"));
    //Obtain value of the code sample
    var id = tag.attr("value"); 
    var str = "/execute/"+id;
    var old = tag.get(0);
    var htmlStr = $(old).html();
    var index = htmlStr.search("<a href");
    var end = htmlStr.indexOf("</a>",index);
   
    //Add a temp Results Pending while the get request is called
    $("<p id = temp>Results Pending</p>").insertBefore(this);
    $(this).remove();
    //Get request to /execute/(value of code sample
    $.get(str, function( data ){
	
	var text = data;
	//Construct new string with the results of the get request
	var newString = htmlStr.substring(0,index-1)+"<p>Output:<br>"+text+"</p>"+htmlStr.substring(end);
	$(tag.get(0)).replaceWith(newString);
    });
    
});
});