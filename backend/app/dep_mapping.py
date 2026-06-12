"""Import-name mapping for packages whose Python import differs from their PyPI name.

Used by both entrypoint.sh (pre-startup dependency verification) and main.py
(health endpoint dependency check) to avoid MAPPING dict duplication.
"""

MAPPING: dict[str, str] = {
    "PyMuPDF": "fitz",
    "Pillow": "PIL",
    "beautifulsoup4": "bs4",
    "python-docx": "docx",
    "python-pptx": "pptx",
    "python-jose": "jose",
    "python-multipart": "multipart",
    "discord.py": "discord",
    "dingtalk-stream": "dingtalk_stream",
    "pycryptodome": "Crypto",
    "lxml-html-clean": "lxml_html_clean",
    "wuying-agentbay-sdk": "agentbay",
    "pydantic-settings": "pydantic_settings",
    "lark-oapi": "lark_oapi",
    "PyNaCl": "nacl",
    "passlib": "passlib",
    "wecom-aibot-sdk-python": "wecom_aibot_sdk",
    "websockets": "websockets",
    "aiofiles": "aiofiles",
    "httpx": "httpx",
    "pyyaml": "yaml",
}
