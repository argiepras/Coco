function refresh(){
    $.ajax({
        url: "/api/stats/",
        method: "GET",
        "dataType": "json",
        success: updatestats,
    })
}

function updatestats(data, status, xhr){
    for(resource in data){
        $("span[id='" + resource + "']").html(data[resource]);
    }
}



function objectify(){
    var cookies = document.cookie;
}