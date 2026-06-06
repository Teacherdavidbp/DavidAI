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

  function statusLabel(status) {
    if (!status) return "Unknown";
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  function feedbackForStatus(status) {
    switch (status) {
      case "sent":
        return "SOS alert created. SMS sent to primary trusted contact.";
      case "failed":
        return "SOS alert created. SMS delivery failed — see notification history.";
      case "simulated":
        return "SOS alert created. Simulated SMS notification recorded.";
      default:
        return "SOS alert created. Notification recorded.";
    }
  }

  function resultClassForStatus(status) {
    if (status === "failed") return "error";
    if (status === "sent") return "success";
    return "success";
  }

  function showNotificationResult(data) {
    if (!notificationResult) return;

    if (data.notification) {
      const n = data.notification;
      const status = n.status || "simulated";
      let html =
        "<h4>SOS alert created</h4>" +
        "<p><strong>Contact:</strong> " + escapeHtml(n.contact_name) + "</p>" +
        "<p><strong>Channel:</strong> SMS</p>" +
        "<p><strong>Status:</strong> " + escapeHtml(statusLabel(status)) + "</p>";

      if (n.provider_sid) {
        html += "<p><strong>Provider ID:</strong> " + escapeHtml(n.provider_sid) + "</p>";
      }
      if (n.provider_detail) {
        html += "<p><strong>Detail:</strong> " + escapeHtml(n.provider_detail) + "</p>";
      }
      html += "<p class=\"sos-notification-preview\">" + escapeHtml(n.message) + "</p>";

      notificationResult.innerHTML = html;
      notificationResult.className = "sos-notification-result " + resultClassForStatus(status);
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
      } else if (data.notification) {
        showFeedback(feedbackForStatus(data.notification.status), data.notification.status === "failed" ? "warning" : "success");
      } else {
        showFeedback("SOS alert created.", "success");
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
        "Trigger SOS alert?\n\nYour GPS location will be saved and your primary trusted contact may receive an SMS if Twilio is enabled."
      )
    ) {
      return;
    }
    triggerSos();
  });

  checkGeolocationSupport();
})();
