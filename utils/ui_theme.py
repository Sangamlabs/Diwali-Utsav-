"""
Dynamic Theming, Typography & Decorative UI Engine for Diwali Bot.
Transforms texts into rich Unicode typographic styles & festive frames.
"""

from typing import Dict, Any, Optional

# --- Unicode Font Translation Tables ---
_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWER = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"

# 1. Bold Sans (Clean & Modern)
_SANS_BOLD_UPPER = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
_SANS_BOLD_LOWER = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
_SANS_BOLD_DIGITS = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"

# 2. Bold Serif (Royal Maharaja)
_SERIF_BOLD_UPPER = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
_SERIF_BOLD_LOWER = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
_SERIF_BOLD_DIGITS = "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"

# 3. Small Caps (Aesthetic & Sleek)
_SMALL_CAPS_UPPER = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
_SMALL_CAPS_LOWER = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"

# 4. Double Struck / Hollow (Outlined Luxury)
_OUTLINE_UPPER = "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
_OUTLINE_LOWER = "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫"
_OUTLINE_DIGITS = "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"

def to_font(text: str, style: str = "bold_sans") -> str:
    """
    Transforms ASCII characters in text to stylized Unicode fonts.
    Supported styles:
    - 'bold_sans': 𝗔𝗕𝗖 / 𝗮𝗯𝗰
    - 'serif_bold': 𝐀𝐁𝐂 / 𝐚𝐛𝐜
    - 'small_caps': ᴀʙᴄ
    - 'outline': 𝔸𝔹ℂ / 𝕒𝕓𝕔
    - 'normal': Standard letters
    """
    if style == "normal" or not text:
        return text

    if style == "bold_sans":
        u_map = dict(zip(_UPPER, _SANS_BOLD_UPPER))
        l_map = dict(zip(_LOWER, _SANS_BOLD_LOWER))
        d_map = dict(zip(_DIGITS, _SANS_BOLD_DIGITS))
    elif style == "serif_bold":
        u_map = dict(zip(_UPPER, _SERIF_BOLD_UPPER))
        l_map = dict(zip(_LOWER, _SERIF_BOLD_LOWER))
        d_map = dict(zip(_DIGITS, _SERIF_BOLD_DIGITS))
    elif style == "small_caps":
        u_map = dict(zip(_UPPER, _SMALL_CAPS_UPPER))
        l_map = dict(zip(_LOWER, _SMALL_CAPS_LOWER))
        d_map = {}
    elif style == "outline":
        u_map = dict(zip(_UPPER, _OUTLINE_UPPER))
        l_map = dict(zip(_LOWER, _OUTLINE_LOWER))
        d_map = dict(zip(_DIGITS, _OUTLINE_DIGITS))
    else:
        return text

    res = []
    for char in text:
        if char in u_map:
            res.append(u_map[char])
        elif char in l_map:
            res.append(l_map[char])
        elif char in d_map:
            res.append(d_map[char])
        else:
            res.append(char)
    return "".join(res)

# --- Theme Layout Configurations ---
THEMES = {
    "royal": {
        "id": "royal",
        "name": "👑 Royal Maharaja",
        "font_style": "serif_bold",
        "top_border": "❖ ═════════════════════ ❖",
        "bottom_border": "❖ ═════════════════════ ❖",
        "divider": "❖ ───────────────────── ❖",
        "bullet": "◆",
        "accent": "✨"
    },
    "celestial": {
        "id": "celestial",
        "name": "🌟 Celestial Festive",
        "font_style": "bold_sans",
        "top_border": "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
        "bottom_border": "✦ ━━━━━━━━━━━━━━━━━━━━━ ✦",
        "divider": "✦ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ✦",
        "bullet": "★",
        "accent": "🌟"
    },
    "sleek": {
        "id": "sleek",
        "name": "💎 Modern Minimal",
        "font_style": "small_caps",
        "top_border": "┌─────────────────────┐",
        "bottom_border": "└─────────────────────┘",
        "divider": "├─────────────────────┤",
        "bullet": "•",
        "accent": "⚡"
    },
    "vedic": {
        "id": "vedic",
        "name": "🪔 Vedic Shubh Deepavali",
        "font_style": "outline",
        "top_border": "══ 🪔 ════════════════ 🪔 ══",
        "bottom_border": "══ 🪔 ════════════════ 🪔 ══",
        "divider": "── 🕯️ ──────────────── 🕯️ ──",
        "bullet": "🪔",
        "accent": "🕉️"
    }
}

DEFAULT_THEME = "royal"

def get_theme(theme_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch theme layout dictionary."""
    if theme_id and theme_id in THEMES:
        return THEMES[theme_id]
    return THEMES[DEFAULT_THEME]

def format_banner(title: str, theme_id: str = "royal", subtitle: str = "") -> str:
    """Format an aesthetic, framed dynamic header."""
    thm = get_theme(theme_id)
    styled_title = to_font(title.upper(), thm["font_style"])
    lines = [
        thm["top_border"],
        f"{thm['accent']}  <b>{styled_title}</b>  {thm['accent']}",
    ]
    if subtitle:
        lines.append(f"<i>{subtitle}</i>")
    lines.append(thm["divider"])
    return "\n".join(lines)

def format_divider(theme_id: str = "royal") -> str:
    """Format theme divider."""
    return get_theme(theme_id)["divider"]

def format_bullet(text: str, theme_id: str = "royal") -> str:
    """Format bullet item."""
    thm = get_theme(theme_id)
    return f"{thm['bullet']} {text}"

