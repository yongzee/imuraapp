(() => {
  // Avoid duplicate buttons if this script is loaded more than once.
  if (document.getElementById("imura-install-btn")) return;

  const isInstalled = () =>
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  if (isInstalled()) return;

  let deferredPrompt = null;

  const button = document.createElement("button");
  button.id = "imura-install-btn";
  button.type = "button";
  button.setAttribute("aria-label", "Install Imura app");
  button.innerHTML = `
    <span aria-hidden="true" style="font-size:19px">↓</span>
    <span>Install Imura</span>
  `;

  // Determine bottom spacing based on device width to clear mobile bottom navigation bar
  const isMobile = window.innerWidth <= 991.98;
  const bottomOffset = isMobile ? "85px" : "22px";

  Object.assign(button.style, {
    position: "fixed",
    right: "20px",
    bottom: bottomOffset,
    zIndex: "99999",
    display: "none", // Hidden by default; revealed only when prompt or iOS fallback is ready
    alignItems: "center",
    justifyContent: "center",
    gap: "9px",
    padding: "13px 20px",
    border: "none",
    borderRadius: "999px",
    background: "#101B35",
    color: "#FFFFFF",
    fontSize: "15px",
    fontWeight: "600",
    fontFamily: "Arial, sans-serif",
    boxShadow: "0 5px 18px rgba(0,0,0,0.22)",
    cursor: "pointer"
  });

  button.addEventListener("mouseenter", () => {
    button.style.background = "#20365F";
  });

  button.addEventListener("mouseleave", () => {
    button.style.background = "#101B35";
  });

  document.body.appendChild(button);

  // Check if browser is iOS (Safari doesn't support beforeinstallprompt)
  const isIOS =
    /iPhone|iPad|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  if (isIOS) {
    // Reveal button for iOS users so they can tap for manual installation instructions
    button.style.display = "flex";
  }

  // Chrome, Edge, Android, and supported Chromium browsers
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
    button.style.display = "flex";
  });

  button.addEventListener("click", async () => {
    if (isInstalled()) {
      button.remove();
      return;
    }

    if (deferredPrompt) {
      const promptEvent = deferredPrompt;
      deferredPrompt = null;

      await promptEvent.prompt();

      const choice = await promptEvent.userChoice;

      if (choice.outcome === "accepted") {
        button.remove();
      }

      return;
    }

    if (isIOS) {
      alert(
        'To install Imura:\n\n' +
        '1. Open this website in Safari.\n' +
        '2. Tap the Share button.\n' +
        '3. Select "Add to Home Screen".\n' +
        '4. Tap "Add".'
      );
    } else {
      alert(
        'To install Imura:\n\n' +
        'Open your browser menu and look for ' +
        '"Install app" or "Add to Home screen". ' +
        'If that option is missing, check that the ' +
        'site is using HTTPS or localhost and that ' +
        'the PWA manifest and service worker are valid.'
      );
    }
  });

  window.addEventListener("appinstalled", () => {
    button.remove();
    deferredPrompt = null;
  });
})();