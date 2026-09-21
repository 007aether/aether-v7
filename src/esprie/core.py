"""ESPRIEAETHER v9 — Unified brain

كل رسالة → فهم → قرار → أداة → رد
"""
import json, re, sqlite3
from datetime import datetime
from .tools import TOOLS, list_tools, call as call_tool
from ..brain import ask, ask_deep
from ..config import DB_PATH
from ..utils import setup_logger, now

log = setup_logger("esprie")

# ═══════════════ أدوات متاحة للـ AI ═══════════════
TOOL_LIST = ", ".join(TOOLS.keys())

SYSTEM_PROMPT = f"""أنت ESPRIEAETHER، عقل رقمي مغربي ذكي ومختصر.

عندك أدوات (tools). كايطلب منك قرار:
- إلا كانت رسالة عادية → رد رد عادي بالدارجة
- إلا كانت طلب أداة → رد JSON بالشكل: {{"tool": "name", "arg": "اختياري"}}

الأدوات المتوفرة: {TOOL_LIST}

أمثلة:
- "شحال عندنا فلوس؟" → {{"tool": "status"}}
- "فحص airdrops" → {{"tool": "airdrops"}}
- "شحال الwallet" → {{"tool": "wallet"}}
- "عمل فيديو على AI" → {{"tool": "make_video", "arg": "AI"}}
- "المحافظ" → {{"tool": "wallet"}}
- "الحالة" → {{"tool": "status"}}

جاوب JSON فقط إلا كانت أداة. رد عادي إلا كان سؤال.
"""

# ═══════════════ الكلمات المفتاحية → أدوات ═══════════════
# أولوية: كلمات خاصة أولاً، ثم عامة
KEYWORDS = {
    # خاصة (فحص أولاً)
    "wallet": ["محفظة", "wallet", "رصيد", "balance", "عنوان"],
    "airdrops": ["airdrop", "ايردروب", "airdrops", "airdrop"],
    "eligibility": ["أهلية", "eligible", "اهلية"],
    "make_video": ["فيديو", "video", "make video"],
    "gas": ["غاز", "gas", "fees", "رسوم"],
    "chains": ["شبكات", "chains", "شبكة"],
    "services": ["services", "خدمات"],
    "depin": ["depin", "mining", "تعدين"],
    "hermes": ["hermes", "هيرمس"],
    "plan": ["خطة", "plan"],
    "content_run": ["محتوى", "content", "script"],
    "market": ["سوق", "market", "أسعار", "اسعار"],
    "report": ["تقرير", "report"],
    "backup": ["backup", "نسخة"],
    "sync": ["مزامنة", "sync"],
    "learn": ["تعلم", "تحليل", "learn"],
    # عامة (آخر شيء)
    "earnings": ["أرباح", "earnings", "ربح"],
    "status": ["status", "إحصائيات", "cycles"],
}

def _detect_tool_keyword(text):
    """كشف أداة من الكلمات المفتاحية (سريع)"""
    text_low = text.lower()
    for tool, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text_low:
                return tool
    return None

def _detect_tool_ai(text):
    """كشف أداة عبر AI (أبطأ ولكن أذكى)"""
    try:
        resp = ask(f"{text}\n\nرد JSON فقط.", SYSTEM_PROMPT)
        # استخرج JSON
        m = re.search(r'\{[^}]+\}', resp)
        if m:
            data = json.loads(m.group(0))
            tool = data.get("tool")
            if tool in TOOLS:
                return tool, data.get("arg")
    except Exception as e:
        log.error(f"ai detect: {e}")
    return None, None

def _log_cycle(obs, decision, action, success=True):
    try:
        c = sqlite3.connect(DB_PATH, timeout=10)
        c.execute(
            "INSERT INTO cycles (ts, observation, decision, action, success) VALUES (?,?,?,?,?)",
            (now(), obs, decision, action, 1 if success else 0),
        )
        c.commit()
        c.close()
    except Exception as e:
        log.error(f"log: {e}")

def process(text, use_ai=False):
    """العملية الرئيسية: نص → نتيجة"""
    text = text.strip()
    if not text:
        return {"type": "empty", "reply": "؟"}

    # 1. كشف أداة (keywords سريع)
    tool_name = _detect_tool_keyword(text)
    arg = None

    # 2. إلا ما لقاش، جرب AI
    if not tool_name and use_ai:
        tool_name, arg = _detect_tool_ai(text)

    # 3. تنفيذ الأداة
    if tool_name and tool_name in TOOLS:
        log.info(f"→ tool: {tool_name}")
        try:
            if tool_name == "make_video":
                result = call_tool(tool_name, arg or text[:50])
            else:
                result = call_tool(tool_name)
            _log_cycle(text, f"tool:{tool_name}", "esprie_call", True)
            return {
                "type": "tool",
                "tool": tool_name,
                "result": result,
            }
        except Exception as e:
            log.error(f"tool {tool_name}: {e}")
            _log_cycle(text, f"tool:{tool_name}", "esprie_call", False)
            return {"type": "error", "tool": tool_name, "error": str(e)}

    # 4. سؤال عام → AI
    log.info("→ AI")
    reply = ask(text) or "..."
    _log_cycle(text, reply[:100], "esprie_ai", True)
    return {"type": "ai", "reply": reply}

def process_deep(text):
    """نسخة hermes3 العميقة"""
    reply = ask_deep(text) or "..."
    _log_cycle(text, reply[:100], "esprie_deep", True)
    return {"type": "deep", "reply": reply}

def info():
    """معلومات عن العقل"""
    return {
        "name": "ESPRIEAETHER",
        "version": "v9",
        "tools": len(TOOLS),
        "tool_list": [t[0] for t in list_tools()],
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        r = process(text)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(info(), indent=2, ensure_ascii=False))
