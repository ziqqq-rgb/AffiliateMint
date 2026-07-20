"""
backend/scraper/intercept.py
Step 3: Network Interception and Background API Capture using CDP Mode.
Acts as a browser wiretap to capture hidden JSON API calls and background XHR data.
"""
import time
import mycdp

class NetworkInterceptor:
    def __init__(self, browser):
        self.browser = browser
        self.captured_requests = []
        self.captured_responses = []
        self.target_keywords = []
        self.is_intercepting = False

    def set_filter_keywords(self, keywords: list):
        self.target_keywords = [kw.lower() for kw in keywords] if keywords else []
        print(f"[+] Active network filter keywords: {self.target_keywords}")

    def _matches_filter(self, url: str) -> bool:
        if not self.target_keywords:
            return True
        url_lower = url.lower()
        return any(kw in url_lower for kw in self.target_keywords)

    def _fetch_cdp_body(self, req_id: str) -> str:
        """Universal CDP Body Fetcher: Supports Undetected ChromeDriver, SeleniumBase, and standard Selenium."""
        driver = self.browser.driver
        params = {"requestId": str(req_id)}
        
        # Method 1: Undetected ChromeDriver / UC Mode (This is what your StealthBrowser uses!)
        if hasattr(driver, "send_command_and_get_result"):
            res = driver.send_command_and_get_result("Network.getResponseBody", params)
            return res.get("body", "") if isinstance(res, dict) else str(res)
            
        # Method 2: Standard Selenium 4
        if hasattr(driver, "execute_cdp_cmd"):
            res = driver.execute_cdp_cmd("Network.getResponseBody", params)
            return res.get("body", "") if isinstance(res, dict) else str(res)
            
        # Method 3: Legacy UC / Selenium send_command
        if hasattr(driver, "send_command"):
            res = driver.send_command("Network.getResponseBody", params)
            return res.get("body", "") if isinstance(res, dict) else str(res)

        raise AttributeError("No valid CDP execution method found on this driver instance.")

    async def _on_request_sent(self, event: mycdp.network.RequestWillBeSent):
        req = event.request
        if self._matches_filter(req.url):
            self.captured_requests.append({
                "url": req.url,
                "method": req.method,
                "headers": req.headers,
                "timestamp": time.time()
            })

    async def _on_response_received(self, event: mycdp.network.ResponseReceived):
        res = event.response
        is_json = "application/json" in str(res.mime_type).lower()
        
        noise_domains = [
            "monitor", "byteoversea", "mcs", "mssdk", "browser-settings", 
            "api-verification", "libraweb", "web-cookie-privacy", "ttwstatic"
        ]
        if any(noise in res.url for noise in noise_domains):
            return

        if self._matches_filter(res.url) or is_json:
            parsed_payload = None
            raw_body = ""
            
            try:
                raw_body = self._fetch_cdp_body(str(event.request_id))
            except Exception as e:
                if res.status == 200:
                    print(f"[WIRETAP NOTICE] Could not read body for {res.url[:50]}... | Err: {e}")

            if raw_body:
                try:
                    import json
                    parsed_payload = json.loads(raw_body)
                    print(f"[WIRETAP SUCCESS] Captured JSON ({len(raw_body)} bytes) from: {res.url[:60]}...")
                except Exception:
                    pass

            self.captured_responses.append({
                "url": res.url,
                "status": res.status,
                "mime_type": res.mime_type,
                "payload": parsed_payload,
                "timestamp": time.time()
            })

    def start_intercepting(self):
        if not self.browser.driver:
            raise Exception("Browser is not running! Start the browser before intercepting traffic.")
        
        print("[+] Attaching CDP network wiretap handlers...")
        self.browser.driver.add_handler(mycdp.network.RequestWillBeSent, self._on_request_sent)
        self.browser.driver.add_handler(mycdp.network.ResponseReceived, self._on_response_received)
        self.is_intercepting = True
        print("[SUCCESS] Network interception is LIVE!")

    def get_captured_data(self) -> dict:
        return {
            "total_requests": len(self.captured_requests),
            "total_responses": len(self.captured_responses),
            "requests": self.captured_requests,
            "responses": self.captured_responses
        }

    def clear_log(self):
        self.captured_requests.clear()
        self.captured_responses.clear()
        print("[+] Intercept log cleared.")