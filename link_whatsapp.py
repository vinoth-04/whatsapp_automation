import time
from pathlib import Path
from app.services.whatsapp_service import WhatsAppClient, SESSION_DIR


def main():
    print("\n" + "=" * 60)
    print("      WHATSAPP LINKED DEVICE SETUP (QR CODE)")
    print("=" * 60)
    print(f"Session directory: {SESSION_DIR.resolve()}")
    print("\nStarting Chrome browser...")

    client = WhatsAppClient(headless=False)
    client.start()

    print("Navigating to WhatsApp Web...")
    client.page.goto("https://web.whatsapp.com", wait_until="load")

    print("\n👉 ACTION REQUIRED:")
    print("1. Open WhatsApp on your phone.")
    print("2. Tap Menu (Android) or Settings (iPhone) -> 'Linked Devices'.")
    print("3. Tap 'Link a Device' and point your camera at the QR code in the Chrome window.\n")
    print("Waiting for QR code scan...")

    try:
        while True:
            # Check if chat list has loaded
            is_ready = client.is_logged_in(timeout_sec=3)
            if is_ready:
                print("\n" + "=" * 60)
                print("🎉 SUCCESS! WhatsApp linked successfully.")
                print(f"Your session is securely saved in:\n{SESSION_DIR}")
                print("You can now run your FastAPI scheduler to send messages automatically.")
                print("=" * 60 + "\n")
                break

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    finally:
        print("Closing browser window...")
        client.close()
        print("Done!")


if __name__ == "__main__":
    main()

