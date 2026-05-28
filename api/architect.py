from http.server import BaseHTTPRequestHandler
import json, os, urllib.request

SYSTEM_PROMPT = """You are WebLens AWS Architect, a senior cloud solutions architect specializing in AWS. 
Help developers design AWS architectures, choose the right services, and stay within free tier limits.

Return ONLY a valid JSON object (no markdown, no extra text):
{
  "architecture_name": "<short catchy name for this architecture>",
  "overview": "<3-4 sentence description of the recommended architecture and why>",
  "services": [
    {
      "name": "<AWS service name e.g. EC2, S3, Lambda>",
      "purpose": "<what it does in this architecture>",
      "tier": "<free|low-cost|paid>",
      "free_tier": "<free tier limit e.g. '750 hrs/month t2.micro' or 'N/A'>",
      "monthly_estimate": "<rough cost estimate e.g. '$0 (free tier)' or '~$5-15'>"
    }
  ],
  "diagram_steps": [
    "<step 1: e.g. User → CloudFront CDN>",
    "<step 2: e.g. CloudFront → ALB>",
    "<step 3: e.g. ALB → EC2 Auto Scaling Group>"
  ],
  "total_estimate": "<total monthly estimate for described setup>",
  "free_tier_safe": <true|false>,
  "warnings": ["<important warning 1>", "<warning 2>"],
  "iac_hint": "<1-2 sentence Terraform or CloudFormation tip for this architecture>"
}

Rules:
- Be specific about AWS service names (not generic descriptions)
- Prioritize free tier services when possible
- max 8 services
- diagram_steps: 3-6 steps showing data flow
- warnings: things that could cause unexpected charges, max 3
- Always be honest about costs — never hide potential charges"""


def call_groq(messages):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.4,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

            description = body.get("description", "").strip()
            requirements = body.get("requirements", [])
            budget = body.get("budget", "free tier")
            scale = body.get("scale", "small")

            if not description:
                return self._error(400, "Project description is required")

            user_msg = f"""Design an AWS architecture for:

Project: {description}
Requirements: {', '.join(requirements) if requirements else 'Not specified'}
Budget: {budget}
Scale: {scale}

Recommend the best AWS services, explain the architecture, and flag any free-tier risks."""

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
