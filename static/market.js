
$(document).ready(function(){
    //setting up buy and sell buttons for ajax
    $('button').click(function(event){
        event.preventDefault();
        $.ajax({
            method: "POST",
            data: {
                "csrfmiddlewaretoken": $("input[name='csrfmiddlewaretoken']").val(),
                'action': this.name,
                'amount': this.value,
                "timestamp": $("input[name='lastchange']").val()
            },
            "dataType": "json",
            success: checkings,
        })
    })
})



function priceupdate(){

}


function checkings(data, status, xhr){
    $('.result').html(data.result);
    $('.result').show();
    if('stats' in data){
        for(resource in data.stats){
            $("span[id='" + resource + "']").html(data.stats[resource]);
        }
    };

    if('prices' in data){
        for(resource in data.prices){
            //setting updated prices
            var search = "td[id='" + resource + "'] b";
            $(search).html(data.prices[resource].price);
            //and flashing the td red or green based on price change
            var element = $("td[id='" + resource + "']");
            if (element.queue().length > 0) {element.stop(true, true)};
            element.effect("highlight", {'color': data.prices[resource].color}, 1500);
        }
    }
}
