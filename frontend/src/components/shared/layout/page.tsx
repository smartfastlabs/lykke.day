import SettingsButton from "../settingsButton";

export default function Page(props) {
  const enablePush = () => {
    console.log("Enabling push notifications...");
    if (Notification.permission === "granted") {
      const notification = new Notification("Ooops ;)", {
        body: "You're already subscribed to push notifications.",
        icon: "/images/icons/jasper/192.png", // Your PWA icon
      });
      notification.onclick = (event) => {
        event.preventDefault(); // Prevent the browser from focusing the Notification's tab
        console.log("Notification clicked!");
        // You can open a new tab, navigate to a specific URL, or perform other actions here
        window.open("https://www.example.com", "_blank");
      };
    } else if ("serviceWorker" in navigator) {
      console.log("Service Worker is supported");
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager
          .subscribe({
            userVisibleOnly: true,
            applicationServerKey:
              "BNWaFxSOKFUzGfVP5DOYhDSS8Nf2W9ifg4_3pNsfEzDih5CfspqP7-Ncr_9jAuwkd8jaHZPHdc0zIqHE-IPDoF8",
          })
          .then(async (subscription) => {
            console.log("Push subscription:", JSON.stringify(subscription));
            const response = await fetch("/api/push/subscribe", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(subscription),
            });
            console.log("Push subscription response:", response);
          })
          .catch((error) => {
            console.error("Push subscription error:", error);
          });
      });
    } else {
      console.error("Service Worker is not supported in this browser.");
    }
  };
  return (
    <div class="overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div class="min-h-screen w-full flex flex-col justify-center typography-body">
        <div class="w-full h-full mx-auto md:px-0 max-w-[960px] mt-4 flex-1 flex flex-col">
          {props.children}
        </div>
      </div>
      <SettingsButton onClick={enablePush} />
    </div>
  );
}
