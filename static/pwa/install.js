(() => {
  // Prevent duplicate banners
  if (document.getElementById("imura-install-banner")) return;

  const isInstalled = () =>
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  // Don't show the banner inside the installed app
  if (isInstalled()) return;

  let deferredPrompt = null;

  const isIOS =
    /iPhone|iPad|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  // Create the banner element
  const banner = document.createElement("div");
  banner.id = "imura-install-banner";

  Object.assign(banner.style, {
    display: "block",
    position: "relative",
    width: "100%",
    boxSizing: "border-box",
    padding: "11px 16px",
    background: "#101B35",
    color: "#FFFFFF",
    fontFamily: "Arial, sans-serif",
    fontSize: "14px",
    lineHeight: "1.4",
    zIndex: "1000"
  });

  banner.innerHTML = `
    <div style="
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      max-width: 1200px;
      margin: 0 auto;
    ">
      <div style="min-width: 0; flex: 1;">
        <strong style="
          display: block;
          font-size: 14px;
          margin-bottom: 2px;
        ">
          Install Imura
        </strong>
        <span style="
          display: block;
          font-size: 12px;
          color: #D8E0F0;
        ">
          Get quicker access from your home screen.
        </span>
      </div>

      <button
        id="imura-install-action"
        type="button"
        style="
          flex-shrink: 0;
          padding: 9px 14px;
          border: 1px solid #FFFFFF;
          border-radius: 8px;
          background: #FFFFFF;
          color: #101B35;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
        ">
        Install
      </button>

      <button
        id="imura-install-dismiss"
        type="button"
        aria-label="Dismiss installation message"
        style="
          flex-shrink: 0;
          padding: 4px;
          border: 0;
          background: transparent;
          color: #FFFFFF;
          font-size: 22px;
          line-height: 1;
          cursor: pointer;
        ">
        &times;
      </button>
    </div>
  `;

  // Insert at the beginning of the page
  document.body.prepend(banner);

  const installAction = banner.querySelector("#imura-install-action");
  const dismissAction = banner.querySelector("#imura-install-dismiss");

  // Remove the banner
  const removeBanner = () => {
    banner.remove();
  };

  // Dismiss the banner
  dismissAction.addEventListener("click", removeBanner);

  // Handle installation or show manual instructions
  installAction.addEventListener("click", async () => {
    if (isInstalled()) {
      removeBanner();
      return;
    }

    if (deferredPrompt) {
      const promptEvent = deferredPrompt;
      deferredPrompt = null;

      try {
        await promptEvent.prompt();
        const choice = await promptEvent.userChoice;

        if (choice.outcome === "accepted") {
          removeBanner();
        }
      } catch (error) {
        console.error("Imura installation prompt failed:", error);
        showManualInstructions();
      }

      return;
    }

    showManualInstructions();
  });

  function showManualInstructions() {
    if (isIOS) {
      alert(
        "To install Imura:\n\n" +
        "1. Open this website in Safari.\n" +
        "2. Tap the Share button.\n" +
        '3. Select "Add to Home Screen".\n' +
        '4. Tap "Add".'
      );
    } else {
      alert(
        "To install Imura:\n\n" +
        "Open your browser menu and look for " +
        '"Install app" or "Add to Home screen".\n\n' +
        "If the option is unavailable, your browser " +
        "may not currently consider the website installable."
      );
    }
  }

  // Capture the browser's native installation event
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
  });

  // Remove the banner after successful installation
  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    removeBanner();
  });

  // Detect if the page switches to standalone display mode
  const displayMode = window.matchMedia("(display-mode: standalone)");

  const handleDisplayModeChange = (event) => {
    if (event.matches) removeBanner();
  };

  if (displayMode.addEventListener) {
    displayMode.addEventListener("change", handleDisplayModeChange);
  } else if (displayMode.addListener) {
    displayMode.addListener(handleDisplayModeChange);
  }
})();