"""AETHER v7.7 — YouTube niche analyzer (for AI content)"""
import json
from ..brain import ask
from ..utils import setup_logger, now

log = setup_logger("yt_niche")

# Niches مع RPP (Revenue Per 1k views)
NICHES = {
    "ai_tools": {"rpm_range": "$7-15", "difficulty": "medium",
                 "note": "AI tools reviews, tutorials"},
    "finance": {"rpm_range": "$15-40", "difficulty": "hard",
                "note": "personal finance, investing"},
    "tech_reviews": {"rpm_range": "$7-15", "difficulty": "medium",
                     "note": "software, gadgets"},
    "health": {"rpm_range": "$4-10", "difficulty": "medium",
               "note": "fitness, self-improvement"},
    "faceless_docs": {"rpm_range": "$2-8", "difficulty": "easy",
                      "note": "documentaries, explainers"},
}

def analyze_niche(niche_key):
    """يحلل niche ويقترح محتوى"""
    niche = NICHES.get(niche_key)
    if not niche:
        return {"error": "unknown niche"}

    prompt = f"""YouTube niche: {niche_key} ({niche['note']}). RPM: {niche['rpm_range']}.

أعطني JSON فقط:
{{"titles": ["عنوان1","عنوان2","عنوان3","عنوان4","عنوان5"], "length_min": 10, "tools": ["أداة1","أداة2"], "keywords": ["kw1","kw2","kw3"]}}"""

    response = ask(prompt)
    try:
        # نظف الـ JSON
        cleaned = response.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1].replace("json", "", 1).strip()
        data = json.loads(cleaned)
    except Exception as e:
        log.error(f"parse: {e}, raw: {response[:200]}")
        data = {"raw": response}

    return {
        "niche": niche_key,
        "rpm": niche["rpm_range"],
        "analysis": data,
    }

def all_niches_summary():
    return {
        k: {"rpm": v["rpm_range"], "difficulty": v["difficulty"], "note": v["note"]}
        for k, v in NICHES.items()
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(analyze_niche(sys.argv[1]), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(all_niches_summary(), indent=2, ensure_ascii=False))
