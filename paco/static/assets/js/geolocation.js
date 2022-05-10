function getDriverLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, showError);
  } else {
    alert("Geolocation is not supported by this browser. Please insert your starting location manually.");
  }
}

function showPosition(position) {
  var elem = document.getElementById("from_location")
  console.log(position.coords.latitude + ", " + position.coords.longitude)
  elem.value = position.coords.latitude + ", " + position.coords.longitude
}

function showError(error) {
  switch(error.code) {
    case error.PERMISSION_DENIED:
      alert("User denied the request for Geolocation. Please insert your starting location manually.")
      break;
    case error.POSITION_UNAVAILABLE:
      alert("Location information is unavailable. Please insert your starting location manually.")
      break;
    case error.TIMEOUT:
      alert("The request to get user location timed out. Please insert your starting location manually.")
      break;
    case error.UNKNOWN_ERROR:
      alert("An unknown error occurred. Please insert your starting location manually.")
      break;
  }
}