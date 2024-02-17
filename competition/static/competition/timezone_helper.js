$(function() {
    var x = document.getElementsByClassName("toLocalTime");
    var offset = new Date().getTimezoneOffset()*60*1000 ;
    for (i = 0; i < x.length; ++i) {
        var d = new Date(0);
        var t = Date.parse(x[i].innerHTML);
        d.setUTCMilliseconds(t - offset);
        x[i].innerHTML = d.toString().replace(/GMT.*/g,"");
    }
    var tz = document.getElementById("tz_str");
    if (tz) {
        tz.innerHTML = new Date().toString().match(/\(([A-Za-z\s].*)\)/)[1];
    }
});

// Function to determine if the date is today, yesterday, or tomorrow
function asReadableDay(localDate){
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    if (localDate.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (localDate.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else if (localDate.toDateString() === tomorrow.toDateString()) {
        return 'Tomorrow';
    } else {
        return daysOfWeek[localDate.getDay()];
    }
}

function toLocalTimeHM(utcDate){
    let localDate = new Date(utcDate);

    let formattedTime = localDate.toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' , hour12: false});

    return `${formattedTime}`;
}
function toLocalTimeHMday(utcDate){
    let localDate = new Date(utcDate);

    let formattedTime = localDate.toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' , hour12: false});
    let formattedDay = asReadableDay(localDate);

    return `${formattedTime} ${formattedDay}`;
}

htmx.onLoad(function(elt){
    var x = elt.getElementsByClassName("toLocalTimeHM");
    for (i = 0; i < x.length; ++i) {
        elem = x[i]
        elem.innerHTML = toLocalTimeHM(elem.innerHTML)
    }

    var list = elt.getElementsByClassName("toLocalTimeHMday");
    for (i = 0; i < list.length; ++i) {
        elem = list[i]
        elem.innerHTML = toLocalTimeHMday(elem.innerHTML)
    }
});
