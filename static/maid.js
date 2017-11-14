
$(document).ready(function(){
    $('a[class="sortie"]').click(function(event){
        event.preventDefault();
        var cookie_value = $(event.target).attr('id');
        if (document.cookie.indexOf('-' + cookie_value) === -1) {
            // order needs to be reverted
            cookie_value = '-' + cookie_value;
        }
        document.cookie = "order_by=" + cookie_value;
        location.reload();
    })
})



function sortaid(event){

}