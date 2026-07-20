"""
backend/scraper/intercept.py
Step 3: Network Interception and Background API Capture using CDP Mode.
Acts as a browser wiretap to capture hidden JSON API calls and background XHR data.
"""
import time
import mycdp

class NetworkInterceptor:
    def __init__(self, browser):
        """Connects the interceptor to an active StealthBrowser instance."""
        self.browser = browser
        self.captured_requests = []
        self.captured_responses = []
        self.target_keywords = []
        self.is_intercepting = False

    def set_filter_keywords(self, keywords: list):
        """Sets URL keywords to filter for specific API calls."""
        self.target_keywords = [kw.lower() for kw in keywords] if keywords else []
        print(f"[+] Active network filter keywords: {self.target_keywords}")

    def _matches_filter(self, url: str) -> bool:
        """Checks if a URL matches our target keywords."""
        if not self.target_keywords:
            return True
        url_lower = url.lower()
        return any(kw in url_lower for kw in self.target_keywords)

    async def _on_request_sent(self, event: mycdp.network.RequestWillBeSent):
        """Internal handler triggered every time Chrome sends a request."""
        req = event.request
        if self._matches_filter(req.url):
            self.captured_requests.append({
                "url": req.url,
                "method": req.method,
                "headers": req.headers,
                "timestamp": time.time()
            })

    async def _on_response_received(self, event: mycdp.network.ResponseReceived):
        """Internal handler triggered every time Chrome receives a response."""
        res = event.response
        is_json = "application/json" in str(res.mime_type).lower()
        
        # Filter out noise domains like monitor or byteoversea telemetry
        noise_domains = ["monitor", "byteoversea", "mcs", "mssdk", "browser-settings"]
        if any(noise in res.url for noise in noise_domains):
            return

        if self._matches_filter(res.url) or is_json:
            parsed_payload = None
            try:
                # 1. CRITICAL: Command CDP to fetch the actual response body from memory!
                body_obj = await self.browser.driver.send(
                    mycdp.network.get_response_body(event.request_id)
                )
                # CDP returns a tuple (body_string, base64_encoded_bool)
                raw_body = body_obj[0] if isinstance(body_obj, tuple) else getattr(body_obj, 'body', str(body_obj))
                
                import json
                parsed_payload = json.loads(raw_body)
            except Exception:
                # Background XHR requests sometimes abort or close before the body is readable
                pass

            self.captured_responses.append({
                "url": res.url,
                "status": res.status,
                "mime_type": res.mime_type,
                "payload": parsed_payload,  # <-- Now storing the actual product JSON!
                "timestamp": time.time()
            })

    def start_intercepting(self):
        """Attaches CDP network event handlers to the live browser session."""
        if not self.browser.driver:
            raise Exception("Browser is not running! Start the browser before intercepting traffic.")
        
        print("[+] Attaching CDP network wiretap handlers...")
        self.browser.driver.add_handler(mycdp.network.RequestWillBeSent, self._on_request_sent)
        self.browser.driver.add_handler(mycdp.network.ResponseReceived, self._on_response_received)
        self.is_intercepting = True
        print("[SUCCESS] Network interception is LIVE!")

    def get_captured_data(self) -> dict:
        """Returns all intercepted requests and responses."""
        return {
            "total_requests": len(self.captured_requests),
            "total_responses": len(self.captured_responses),
            "requests": self.captured_requests,
            "responses": self.captured_responses
        }

    def clear_log(self):
        """Wipes captured arrays clean."""
        self.captured_requests.clear()
        self.captured_responses.clear()
        print("[+] Intercept log cleared.")