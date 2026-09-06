"""
Kisan Dost — Pest & Disease Doctor Tool
=========================================
Identifies pests and diseases from symptoms and prescribes safe treatments.
Returns typed PestDiagnosis Pydantic model.
Validates inputs and handles missing symptoms or unknown ailments gracefully.
"""

from __future__ import annotations

from agents import function_tool
from models.schemas import PestDiagnosis

PEST_KNOWLEDGE_BASE = [
    {
        "id": "whitefly",
        "name": "Whitefly (Safed Makhi)",
        "crops": ["cotton", "kapas", "tomato", "vegetables", "chilli", "okra", "bhindi"],
        "keywords": ["whitefly", "safed makhi", "white fly", "makhi", "honeydew", "sticky", "sooty mold", "curling", "yellow leaves"],
        "treatment": "Spray Pyriproxyfen 10.8% EC (for nymphs) or Acetamiprid 20% SP. Ensure full coverage on leaf undersides early morning or late evening.",
        "dosage_ml_per_liter": 2.5,
        "max_safe_dosage_ml_per_liter": 4.0,
        "requires_expert": False,
    },
    {
        "id": "bollworm",
        "name": "Bollworm Complex (Sundi / Pink Bollworm)",
        "crops": ["cotton", "kapas", "maize", "makki", "chickpea", "chana"],
        "keywords": ["bollworm", "sundi", "pink bollworm", "gulabi sundi", "armyworm", "lashkari", "holes in bolls", "caterpillar", "tindi"],
        "treatment": "Spray Emamectin Benzoate 1.9% EC or Chlorantraniliprole. Deploy pheromone delta traps (5-8 per acre) for monitoring.",
        "dosage_ml_per_liter": 2.0,
        "max_safe_dosage_ml_per_liter": 3.0,
        "requires_expert": False,
    },
    {
        "id": "rust",
        "name": "Wheat Rust / Yellow Rust (Kundi / Zangar)",
        "crops": ["wheat", "gandum"],
        "keywords": ["rust", "kundi", "zangar", "yellow stripes", "orange pustules", "brown spots on leaves", "powdery"],
        "treatment": "Foliar spray with Propiconazole 25% EC (Tilt) or Tebuconazole 25.9% EC at first sign of pustules. Repeat after 14 days if needed.",
        "dosage_ml_per_liter": 2.0,
        "max_safe_dosage_ml_per_liter": 3.0,
        "requires_expert": False,
    },
    {
        "id": "aphid",
        "name": "Aphids (Tela / Siah Tela)",
        "crops": ["wheat", "gandum", "mustard", "sarson", "canola", "vegetables"],
        "keywords": ["aphid", "tela", "siah tela", "greenfly", "small green insects", "clusters on ears", "chote keeray"],
        "treatment": "Spray Acetamiprid 20% SP (1.25 g/L) or Flonicamid 50% WDG. Conserve beneficial ladybird beetles in the field.",
        "dosage_ml_per_liter": 1.25,
        "max_safe_dosage_ml_per_liter": 2.5,
        "requires_expert": False,
    },
    {
        "id": "stem_borer",
        "name": "Stem Borer (Tana Chhedak)",
        "crops": ["rice", "chawal", "sugarcane", "ganna", "maize", "makki"],
        "keywords": ["stem borer", "tana chhedak", "dead heart", "white head", "borer", "hollow stem"],
        "treatment": "Apply Cartap hydrochloride 4G granules in standing field water or foliar spray with Chlorantraniliprole 18.5% SC.",
        "dosage_ml_per_liter": 1.5,
        "max_safe_dosage_ml_per_liter": 2.5,
        "requires_expert": False,
    },
    {
        "id": "leaf_curl_virus",
        "name": "Cotton Leaf Curl Virus (CLCuV)",
        "crops": ["cotton", "kapas"],
        "keywords": ["leaf curl", "clcuv", "vein thickening", "enation", "curling upward", "murjhana"],
        "treatment": "No direct chemical cure for virus. Manage whitefly insect vector immediately with Diafenthiuron or Flonicamid. Roguing out severely infected plants.",
        "dosage_ml_per_liter": 2.0,
        "max_safe_dosage_ml_per_liter": 3.0,
        "requires_expert": True,
    },
]


@function_tool
def pest_disease_doctor(symptoms: str, crop: str) -> PestDiagnosis:
    """Diagnose pest or disease and prescribe safe treatment.

    Args:
        symptoms: Description of visible symptoms observed by the farmer.
        crop: The affected crop name (e.g. 'cotton', 'wheat', 'rice').
    """
    # ── Validation ──
    symptoms_clean = symptoms.strip().lower() if symptoms else ""
    crop_clean = crop.strip().lower() if crop else ""

    if not symptoms_clean and not crop_clean:
        return PestDiagnosis(
            likely_pest_or_disease="Unspecified (No symptoms or crop provided)",
            confidence="low",
            treatment="Barah-e-karam fasal ka naam aur nishaniyan (symptoms) batayein taake sahi ilaj tajweez kiya ja sake.",
            dosage_ml_per_liter=0.0,
            max_safe_dosage_ml_per_liter=0.0,
            requires_expert_consultation=True,
        )

    if not symptoms_clean:
        return PestDiagnosis(
            likely_pest_or_disease=f"Unclear issue on {crop_clean.title()}",
            confidence="low",
            treatment=f"{crop_clean.title()} fasal par kya nishaniyan hain (maslan patte peele, keeray, surakh)? Tafseel batayein.",
            dosage_ml_per_liter=0.0,
            max_safe_dosage_ml_per_liter=0.0,
            requires_expert_consultation=True,
        )

    # Search for match in knowledge base
    best_match = None
    highest_score = 0

    for item in PEST_KNOWLEDGE_BASE:
        score = 0
        # Check crop match
        crop_match = any(c in crop_clean for c in item["crops"]) or crop_clean == ""
        if crop_match:
            score += 2

        # Check keyword matches in symptoms
        for kw in item["keywords"]:
            if kw in symptoms_clean:
                score += 3

        if score > highest_score:
            highest_score = score
            best_match = item

    if best_match and highest_score >= 3:
        confidence = "high" if highest_score >= 5 else "medium"
        return PestDiagnosis(
            likely_pest_or_disease=best_match["name"],
            confidence=confidence,
            treatment=best_match["treatment"],
            dosage_ml_per_liter=best_match["dosage_ml_per_liter"],
            max_safe_dosage_ml_per_liter=best_match["max_safe_dosage_ml_per_liter"],
            requires_expert_consultation=best_match["requires_expert"],
        )

    # Graceful fallback when no specific match is found
    return PestDiagnosis(
        likely_pest_or_disease="General Pest/Fungal Infection",
        confidence="low",
        treatment="Nishaniyan kisi aam keere ya phaphoondi (fungus) ki maloom hoti hain. Neem oil spray karein ya qarebi agriculture extension officer ko sample dikhayein.",
        dosage_ml_per_liter=2.0,
        max_safe_dosage_ml_per_liter=3.5,
        requires_expert_consultation=True,
    )
