(function () {
  const sosBtn = document.getElementById("sos-btn");
  const gpsValue = document.getElementById("gps-value");
  const feedback = document.getElementById("sos-feedback");
  const notificationResult = document.getElementById("sos-notification-result");

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
    if (notificationResult) notificationResult.className = "sos-notification-result hidden";
  }

  function showNotificationResult(data) {
    if (!notificationResult) return;

    if (data.notification) {
      const n = data.notification;
      notificationResult.innerHTML =
        "<h4>SOS alert created</h4>" +
        "<p><strong>Would notify:</strong> " + escapeHtml(n.contact_name) + "</p>" +
        "<p><strong>Channel:</strong> SMS (simulated)</p>" +
        "<p><strong>Status:</strong> Simulated</p>" +
        "<p class=\"sos-notification-preview\">" + escapeHtml(n.message) + "</p>";
      notificationResult.className = "sos-notification-result success";
      return;
    }

    if (data.warning) {
      notificationResult.innerHTML =
        "<h4>SOS alert created</h4>" +
        "<p class=\"sos-warning-text\">" + escapeHtml(data.warning) + "</p>" +
        "<p><a href=\"/contacts\">Add a primary trusted contact</a></p>";
      notificationResult.className = "sos-notification-result warning";
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
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

      if (data.warning) {
        showFeedback(data.warning, "warning");
      } else {
        showFeedback("SOS alert created. Simulated SMS notification recorded.", "success");
      }
      showNotificationResult(data);

      setTimeout(function () {
        window.location.reload();
      }, 3500);
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
        "Trigger SOS alert?\n\nYour GPS location will be saved. SMS is simulated only — no real message is sent."
      )
    ) {
      return;
    }
    triggerSos();
  });

  checkGeolocationSupport();
})();
