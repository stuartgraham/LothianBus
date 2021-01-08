
let update_area = document.getElementById("update-area")
function getLocation(){
  if (navigator.geolocation) {
      current_position = navigator.geolocation.getCurrentPosition(showPosition //, errorPosition,
        // {
        //     timeout: 0,
        //     enableHighAccuracy: false,
        //     maximumAge: Infinity
        // }
      );

    } else {
      update_area.innerHTML = "Geolocation is not supported by this browser.";
    } 
}

function showPosition(position) {
  update_area.innerHTML = "Latitude: " + position.coords.latitude +
    "<br>Longitude: " + position.coords.longitude;
    getLiveStopsLocations(position);
  }

function errorPosition(position) {
  update_area.innerHTML = "Cant find location";
  }

async function getLiveStopsLocations(position){
  let lat = position.coords.latitude
  let long = position.coords.longitude
  let api_part = "api/v1/getstops/"
  const api_url = '/' + api_part + lat + '/' + long;
  const response = await fetch(api_url);
  const data = await response.json();
  addStopRadios(data);
}


function addStopRadios(data){
  let stop_tbody = document.getElementById("stop_tbody")
  for (i = 0; i < 10; i++) {
    let tr_stop_radio_row = document.createElement("TR");
    let td_stop_radio_col = document.createElement("TD");
    let stop_radio = document.createElement("INPUT");
    stop_radio.setAttribute("type", "radio");
    td_stop_radio_col.append(stop_radio);

    let td_stop_label_col = document.createElement("TD");
    let stop_label = document.createElement("LABEL");
    let stop_label_text = document.createTextNode(data['stops'][i]['name'] + " (" + data['stops'][i]['direction'] + ")");
    stop_label.appendChild(stop_label_text);
    td_stop_label_col.append(stop_label);
    tr_stop_radio_row.append(td_stop_radio_col);
    tr_stop_radio_row.append(td_stop_label_col);
    stop_tbody.appendChild(tr_stop_radio_row);
  
    }
  drawMap(data['stops'][0]);
  }

function drawMap(data){
  L.mapbox.accessToken = 'pk.eyJ1Ijoic3R1YXJ0Z3JhaGFtIiwiYSI6ImNrYjl0anNxMjBkaDMycW5sZzlybDE5eTcifQ.SqU0SwtoxZEZA1qhMefcsA';
  var map = L.mapbox.map('stop_map_area')
    .setView([data['latitude'], data['longitude']], 9)
    .addLayer(L.mapbox.styleLayer('mapbox://styles/mapbox/streets-v11'));
}
