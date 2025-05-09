from typing import Dict, List, Any
from .enhanced_phonetic_service import is_llm_prominent_phonetic_match


def compare_trademarks_enhanced(
    existing_trademark: Dict[str, Any],
    proposed_name: str,
    proposed_class: str,
    proposed_goods_services: str,
    phonetic_threshold: int = 90,
) -> Dict[str, Any]:
    """
    Enhanced trademark comparison using prominent element analysis.
    """
    # Extract existing trademark details
    existing_name = existing_trademark.get("trademark_name", "").strip()
    existing_class = existing_trademark.get("international_class_number", [])
    existing_goods = existing_trademark.get("goods_services", "").strip()

    # Condition 1: Name-based similarity (using enhanced phonetic matching)
    phonetic_analysis = is_llm_prominent_phonetic_match(
        existing_name, proposed_name, threshold=phonetic_threshold
    )

    # Condition 2: Class overlap
    class_overlap = (
        any(str(c) in str(proposed_class) for c in existing_class)
        if existing_class
        else False
    )

    # Condition 3: Goods/Services overlap
    goods_overlap = bool(
        existing_goods
        and proposed_goods_services
        and any(
            word in proposed_goods_services.lower()
            for word in existing_goods.lower().split()
        )
    )

    # Determine conflict grade
    conditions_met = sum([phonetic_analysis["is_match"], class_overlap, goods_overlap])

    conflict_grade = "No Conflict"
    if conditions_met == 3:
        conflict_grade = "High"
    elif conditions_met == 2:
        conflict_grade = "Moderate"
    elif conditions_met == 1:
        conflict_grade = "Low"

    # If there's a name match but no other conditions, it's a "Name-Match"
    if phonetic_analysis["is_match"] and conditions_met == 1:
        conflict_grade = "Name-Match"

    return {
        "existing_trademark": existing_trademark,
        "proposed_name": proposed_name,
        "proposed_class": proposed_class,
        "proposed_goods_services": proposed_goods_services,
        "phonetic_analysis": phonetic_analysis,
        "class_overlap": class_overlap,
        "goods_overlap": goods_overlap,
        "conditions_met": conditions_met,
        "conflict_grade": conflict_grade,
        "reasoning": generate_conflict_reasoning(
            phonetic_analysis, class_overlap, goods_overlap, conflict_grade
        ),
    }


def generate_conflict_reasoning(
    phonetic_analysis: Dict[str, Any],
    class_overlap: bool,
    goods_overlap: bool,
    conflict_grade: str,
) -> str:
    """
    Generate detailed reasoning for the conflict assessment.
    """
    reasoning_parts = []

    # Add prominent element analysis
    if phonetic_analysis["used_llm"]:
        reasoning_parts.append(
            f"LLM identified prominent elements: '{phonetic_analysis['prominent_element1']}' "
            f"and '{phonetic_analysis['prominent_element2']}'"
        )
    else:
        reasoning_parts.append(
            f"Fallback strategy identified prominent elements: '{phonetic_analysis['prominent_element1']}' "
            f"and '{phonetic_analysis['prominent_element2']}'"
        )

    # Add phonetic analysis
    if phonetic_analysis["exact_match"]:
        reasoning_parts.append("Phonetic codes match exactly")
    else:
        reasoning_parts.append(
            f"Phonetic similarity score: {phonetic_analysis['fuzzy_score']}% "
            f"(threshold: {phonetic_analysis['threshold']}%)"
        )

    # Add class and goods analysis
    if class_overlap:
        reasoning_parts.append("International classes overlap")
    if goods_overlap:
        reasoning_parts.append("Goods/Services overlap")

    # Add conflict grade explanation
    reasoning_parts.append(f"\nConflict Grade: {conflict_grade}")
    if conflict_grade == "High":
        reasoning_parts.append(
            "All three conditions are met: prominent element similarity, class overlap, and goods/services overlap"
        )
    elif conflict_grade == "Moderate":
        reasoning_parts.append("Two conditions are met")
    elif conflict_grade == "Low":
        reasoning_parts.append("One condition is met")
    elif conflict_grade == "Name-Match":
        reasoning_parts.append("Names are similar but no other conditions are met")
    else:
        reasoning_parts.append("No significant conflict detected")

    return "\n".join(reasoning_parts)
