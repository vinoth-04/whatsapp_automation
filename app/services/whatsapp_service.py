import os
import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SESSION_DIR = DATA_DIR / "whatsapp_session"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)


class WhatsAppClient:
    """Manages WhatsApp Web session via Playwright."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self):
        """Initializes browser with persistent context."""
        if self.context:
            return

        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self.playwright = sync_playwright().start()

        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            channel="chrome",
            headless=self.headless,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

    def close(self):
        """Closes browser context."""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
        finally:
            self.context = None
            self.playwright = None
            self.page = None

    def is_logged_in(self, timeout_sec: int = 15) -> bool:
        """Checks if WhatsApp Web is authenticated and chat list is visible."""
        self.start()
        if not self.page:
            return False

        if "web.whatsapp.com" not in self.page.url:
            self.page.goto("https://web.whatsapp.com", wait_until="load")

        # Check for chat list side panel or search bar which confirms authentication
        selectors = [
            "#pane-side",
            "div[aria-label='Chat list']",
            "div[role='textbox'][data-tab='3']"
        ]

        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            for sel in selectors:
                if self.page.query_selector(sel):
                    return True
            # Also check if QR canvas exists (means not logged in)
            if self.page.query_selector("canvas"):
                return False
            time.sleep(1)

        return False

    def send_message(self, phone_number: str, message: str) -> tuple[bool, str]:
        """
        Sends a WhatsApp message via WhatsApp Web direct send URL.
        Returns: (success: bool, info_or_error: str)
        """
        # Clean phone number (strip '+', spaces, dashes, parentheses)
        clean_phone = re.sub(r"[^\d]", "", phone_number)
        encoded_msg = urllib.parse.quote(message)
        send_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

        self.start()
        if not self.page:
            return False, "Failed to start browser session"

        try:
            print(f"[WhatsApp] Navigating to chat for {clean_phone}...")
            self.page.goto(send_url, wait_until="load")

            # Check if logged in or waiting for QR
            qr_canvas = self.page.query_selector("canvas")
            if qr_canvas and not self.page.query_selector("#pane-side"):
                return False, "WhatsApp session not logged in. Please scan QR code first."

            # Wait for either the send button/textbox or invalid number alert
            # WhatsApp loads the chat and automatically puts the message into the textbox
            start_time = time.time()
            max_wait = 30  # 30 seconds max for chat to load

            while time.time() - start_time < max_wait:
                # Check for "Phone number shared via url is invalid" popup
                popup = self.page.query_selector("div[data-animate-modal-popup='true']")
                if popup:
                    popup_text = popup.inner_text()
                    if "invalid" in popup_text.lower() or "ok" in popup_text.lower():
                        return False, f"Invalid phone number or not on WhatsApp: {popup_text.strip()}"

                # Look for send button or active message box
                send_button = self.page.query_selector("button[aria-label='Send']") or self.page.query_selector("span[data-icon='send']")
                
                if send_button:
                    # Give WhatsApp a brief moment to ensure text is fully parsed
                    time.sleep(1)
                    send_button.click()
                    print(f"[WhatsApp] Clicked Send button for {clean_phone}!")
                    
                    # Wait briefly for message to dispatch
                    time.sleep(3)
                    return True, f"wa-web-{int(time.time())}"

                # Fallback: if message box is focused, press Enter
                msg_box = self.page.query_selector("div[contenteditable='true'][data-tab='10']")
                if msg_box:
                    time.sleep(1)
                    msg_box.focus()
                    self.page.keyboard.press("Enter")
                    print(f"[WhatsApp] Pressed Enter in textbox for {clean_phone}!")
                    time.sleep(3)
                    return True, f"wa-web-{int(time.time())}"

                time.sleep(1)

            return False, "Timeout waiting for WhatsApp chat to load."

        except Exception as e:
            return False, f"Exception during message dispatch: {str(e)}"


# Singleton client for scheduler use
_client_instance: WhatsAppClient | None = None


def get_whatsapp_client(headless: bool = True) -> WhatsAppClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = WhatsAppClient(headless=headless)
    return _client_instance

