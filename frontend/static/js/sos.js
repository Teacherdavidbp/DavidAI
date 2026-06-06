(function () {
  const sosBtn = document.getElementById("sos-btn");
  const gpsValue = document.getElementById("gps-value");
  const feedback = document.getElementById("sos-feedback");

  if (!sosBtn || !gpsValue) return;

  function setGpsStatus(text, level) {
    gpsValue.textContent = text;
    gpsValue.className = "gps-value" + (level ? " gps-" + level : "");
  }

  function showFeedback(message, type) {
    if (!feedback) return;
    feedback.textContent = message;
    feedback.className = "sos-feedback " + type;
  }

  function hideFeedback() {
    if (feedback) feedback.className = "sos-feedback hidden";
  }

  function checkGeolocationSupport() {
    if (!navigator.geolocation) {
      setGpsStatus("Not supported in this browser", "error");
      return false;
    }
    setGpsStatus("Ready — location requested when you press SOS", "ok");
    return true;
  }

  function getPosition() {
    return new Promise(function (resolve, reject) {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      });
    });
  }

  function geolocationErrorMessage(err) {
    if (!err || !err.code) {
      return "GPS unavailable. Try again outdoors with location enabled.";
    }
    switch (err.code) {
      case 1:
        return "Location permission denied. Allow GPS access in your browser settings.";
      case 2:
        return "GPS position unavailable. Check device location services.";
      case 3:
        return "GPS request timed out. Try again.";
      default:
        return "Could not get your location. Please try again.";
    }
  }

  async function triggerSos() {
    if (!checkGeolocationSupport()) {
      showFeedback("Geolocation is not supported on this device.", "error");
      return;
    }

    hideFeedback();
    sosBtn.disabled = true;
    setGpsStatus("Getting your location…", "warn");

    try {
      const position = await getPosition();
      const latitude = position.coords.latitude;
      const longitude = position.coords.longitude;

      setGpsStatus(
        "Located: " + latitude.toFixed(5) + ", " + longitude.toFixed(5),
        "ok"
      );

      const response = await fetch("/sos/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: latitude, longitude: longitude }),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Failed to create SOS alert.");
      }

      showFeedback(
        "SOS alert created. Your location has been saved. Help is not notified yet in Phase 1.",
        "success"
      );

      setTimeout(function () {
        window.location.reload();
      }, 1500);
    } catch (err) {
      const message =
        err && err.code !== undefined
          ? geolocationErrorMessage(err)
          : err.message || "SOS failed. Please try again.";
      setGpsStatus(message, "error");
      showFeedback(message, "error");
    } finally {
      sosBtn.disabled = false;
    }
  }

  sosBtn.addEventListener("click", function () {
    if (
      !window.confirm(
        "Trigger SOS alert?\n\nYour GPS location will be saved. No SMS or email is sent in Phase 1."
      )
    ) {
      return;
    }
    triggerSos();
  });

  checkGeolocationSupport();
})();
