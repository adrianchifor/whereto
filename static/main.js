var lastLatLng = { lat: 50.485, lng: 6.064 };
if (localStorage.getItem("latlng") != null) {
    lastLatLng = JSON.parse(localStorage.getItem("latlng"));
}
var lastZoom = 5;
if (localStorage.getItem("zoom") != null) {
    lastZoom = localStorage.getItem("zoom");
}

var mymap = L.map('mapid').setView(lastLatLng, lastZoom);
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    noWrap: true,
    accessToken: 'pk.eyJ1IjoiYWRyaWFuY2hpZm9yIiwiYSI6ImNreHBhNjJmcTA3dWcyb255MTN0aWM0YTEifQ.Ch3q7L9PbLfG0P7utfhRuw'
}).addTo(mymap);

var popup = L.popup();
var circle = L.circle([], {
    color: 'green',
    fillColor: '#00FF00',
    fillOpacity: 0.03
});

var lastRadius = 300000;
if (localStorage.getItem("radius") != null) {
    let radius = localStorage.getItem("radius");
    lastRadius = parseInt(radius) * 1000;
    document.getElementById("radiusSlider").value = radius;
    document.getElementById("radiusText").innerHTML = "Radius " + radius + "km";
}

function updateRadius(value) {
    localStorage.setItem("radius", value);
    lastRadius = parseInt(value) * 1000
    circle.setRadius(lastRadius);
    document.getElementById("radiusText").innerHTML = "Radius " + value + "km";
    return false;
}

var citiesLayerGroup = null;

async function getWeather() {
    cascadeCards(false);
    if (citiesLayerGroup != null) {
        citiesLayerGroup.clearLayers();
    }
    try {
        let request = await fetch(`/api/weather?lat=${lastLatLng.lat}&lon=${lastLatLng.lng}&radius=${lastRadius / 1000}`);
        let response = await request.json();
        if (response["error"] != undefined) {
            throw response["error"];
        }
        if (response["detail"] != undefined) {
            throw response["detail"];
        }
        clearCards();
        fillCards(response);

        let cityMarkers = [];
        Object.keys(response).forEach((city) => {
            let marker = L.marker([response[city]["lat"], response[city]["lon"]]);
            marker.bindPopup(city.replace("/", ", "));
            cityMarkers.push(marker);
        });
        citiesLayerGroup = L.layerGroup(cityMarkers);
        citiesLayerGroup.addTo(mymap);

        setTimeout(function () {
            cascadeCards(true);
            setTimeout(function () {
                mymap.closePopup(popup);
            }, 2000);
        }, 300);
    } catch (err) {
        mymap.closePopup(popup);
        popup.setLatLng(lastLatLng)
            .setContent(String(err))
            .openOn(mymap);
        setTimeout(function () {
            mymap.closePopup(popup);
        }, 6000);
    }
}

const today = new Date();

function fillCards(weather) {
    let dates = [];
    for (let i = 0; i <= 7; i++) {
        let date = new Date(today);
        date.setDate(today.getDate() + i);
        let day = String(date.getDate());
        if (day.length == 1) {
            day = "0" + day;
        }
        let month = String(date.getMonth() + 1);
        if (month.length == 1) {
            month = "0" + month;
        }
        dates.push(day + "/" + month);
    }

    Object.keys(weather).forEach((city, index) => {
        let cityPrefix = String("city" + (index + 1));
        document.getElementById(cityPrefix + "Title").innerHTML = city.replace("/", ", ");
        dates.forEach((date, dateIndex) => {
            if (weather[city][date] == undefined) {
                return;
            }
            let datePrefix = String("Date" + (dateIndex + 1));
            document.getElementById(cityPrefix + datePrefix + "Icon").src = "/static/images/" + weather[city][date]['weather']['icon'] + ".png";
            document.getElementById(cityPrefix + datePrefix + "Icon").alt = weather[city][date]["weather"]["description"];
            document.getElementById(cityPrefix + datePrefix + "Icon").title = weather[city][date]["weather"]["description"];
            let dateMinMax = String(Math.round(weather[city][date]["temp"]["min"]) + "° " + Math.round(weather[city][date]["temp"]["max"]) + "°");
            let popInt = parseInt(weather[city][date]["pop"] * 100);
            let datePop = String(parseInt(weather[city][date]["pop"] * 100) + "%");
            if (popInt > 0) {
                datePop = datePop + "☔";
            }
            document.getElementById(cityPrefix + datePrefix + "Info").innerHTML = date + "<br>" + dateMinMax + "<br>" + datePop;
        });
    });
}

function clearCards() {
    for (let i = 1; i <= 10; i++) {
        let cityPrefix = String("city" + i);
        document.getElementById(cityPrefix + "Title").innerHTML = "";
        for (let j = 1; j <= 8; j++) {
            let datePrefix = String("Date" + j);
            document.getElementById(cityPrefix + datePrefix + "Icon").src = "/static/images/50d.png";
            document.getElementById(cityPrefix + datePrefix + "Info").innerHTML = "";
        }
    }
}

function cardOpacity(card, opacity) {
    document.getElementById(card).style["opacity"] = opacity;
}

function cascadeCards(yes) {
    for (let i = 1; i <= 10; i++) {
        if (yes) {
            setTimeout(function () { cardOpacity("city" + i.toString(), "0.9"); }, 100 + (i * 40));
        } else {
            setTimeout(function () { cardOpacity("city" + i.toString(), "0.2"); }, 100 + (i * 40));
        }
    }
}

function hoverCards(yes) {
    for (let i = 1; i <= 10; i++) {
        let card = "city" + i.toString();
        let currentOpacity = document.getElementById(card).style["opacity"];
        if (yes && currentOpacity == "0.9") {
            cardOpacity(card, "1");
        } else if (!yes && currentOpacity == "1") {
            cardOpacity(card, "0.9");
        }
    }
}

function highlightPoint(latlng) {
    popup.setLatLng(latlng)
        .setContent("Fetching weather for largest cities ...")
        .openOn(mymap);
    circle.setLatLng(latlng)
        .setRadius(lastRadius)
        .addTo(mymap);
    mymap.setView(latlng);
}

function onMapClick(e) {
    lastLatLng = e.latlng;
    highlightPoint(e.latlng);
    localStorage.setItem("latlng", JSON.stringify(e.latlng));
    localStorage.setItem("zoom", mymap.getZoom());
    getWeather();
}

mymap.on('click', onMapClick);
document.getElementById("cards").addEventListener("mouseover", (e) => { hoverCards(true) }, false);
document.getElementById("cards").addEventListener("mouseout", (e) => { hoverCards(false) }, false);

highlightPoint(lastLatLng);
getWeather();
