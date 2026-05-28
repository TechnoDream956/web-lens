from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.error, urllib.parse
import re

SYSTEM_PROMPT = """You are WebLens, an expert web intelligence AI. You receive the raw text content of a webpage and a user query.

Your job:
1. If query is "summarize" or empty: Give a structured summary
2. Otherwise: Answer the user's specific question about the content

Return ONLY a valid JSON object (no markdown, no extra text):
{
  "title": "<page title or best guess>",
  "type": "<article|documentation|github|stackoverflow|blog|news|other>",
  "summary": "<3-5 sentence summary of the main content>",
  "key_points": ["<point 1>", "<point 2>", "<point 3>"],
  "answer": "<direct answer to user's question, or null if just summarizing>",
  "topics": ["<topic tag 1>", "<topic tag 2>", "<topic tag 3>"],
  "read_time": "<estimated read time e.g. '4 min read'>"
}

Rules:
- Be precise and factual based on the content provided
- key_points: max 5, most important insights from the page
- topics: 2-4 short tags describing the content
- If content is too short or invalid, still return valid JSON with what you can infer"""


def call_groq(messages, max_tokens=1200):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_url(url):
    """Fetch a URL and return cleaned text content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; WebLens/1.0; +https://github.com/TechnoDream956)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content_type = resp.headers.get("Content-Type", "")
        if "text" not in content_type and "json" not in content_type:
            raise ValueError(f"Cannot analyze this content type: {content_type}")
        raw = resp.read(400_000)  # max 400KB
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].strip().split(";")[0].strip()
        try:
            return raw.decode(encoding, errors="replace")
        except Exception:
            return raw.decode("utf-8", errors="replace")


def clean_html(html):
    """Strip HTML tags and clean text for AI consumption."""
    # Remove scripts, styles, nav, footer, header
    for tag in ["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe"]:
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
               .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Truncate to ~6000 words for AI context
    words = text.split()
    if len(words) > 6000:
        text = " ".join(words[:6000]) + " [content truncated]"
    return text


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            url = body.get("url", "").strip()
            query = body.get("query", "summarize").strip() or "summarize"

            if not url:
                return self._error(400, "URL is required")

            # Fetch & clean the page
            try:
                raw_html = fetch_url(url)
                text = clean_html(raw_html)
                if len(text) < 100:
                    return self._error(422, "Page content too short or could not be read")
            except urllib.error.URLError as e:
                return self._error(422, f"Could not fetch URL: {str(e.reason)}")
            except urllib.error.HTTPError as e:
                return self._error(422, f"Page returned HTTP {e.code}")
            except Exception as e:
                return self._error(422, f"Fetch error: {str(e)}")

            # Call Groq
            user_msg = f"URL: {url}\nUser query: {query}\n\nPage content:\n{text}"
            result = call_groq([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ])

            raw = result["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
            data["url"] = url

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        except json.JSONDecodeError as e:
            self._error(500, f"AI returned invalid JSON: {str(e)}")
        except Exception as e:
            self._error(500, str(e))

    def _error(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())
