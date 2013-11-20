//form edit_post/postid

$( document ).ready(function() {
    $('.edit_button').click(function ()
{
    var tag = $($(this).parents(".post"));
    var div = tag.children(".comment_body");
    var id = tag.attr("id");
    var str = "/raw/"+id;
 
    $.get(str, function( data ) {
	var text = data;
	$(div.get(0)).replaceWith('<div class="comment_body"><form method="post" action="edit/'+id+'"><input type="hidden" name="thread_id" value="1"><textarea rows="5" cols="45" name="new_content" id="textbox'+id+'"></textarea><br><input id = "sub'+id+'" type="submit" value="Submit"></form></div>');
    var TheTextBox = document.getElementById("textbox"+id);
    TheTextBox.value = text;
    $('#sub'+id).click(function (){
	 setTimeout(function() {document.location = document.URL; } , 500);
    });
    });
});

    $('.delete_button').click(function () {
        var tag = $($(this).parents(".post"));
        var div = tag.children(".comment_body");
        var id = tag.attr("id");
        $.post("/delete_post", {"comment_id" : id, "url" : document.URL});
    });
});


		    


