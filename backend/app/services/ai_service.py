"""AI civic issue detection with an explicit offline demo fallback."""
import json
import logging
from typing import Any, Optional
from backend.app.config import settings

logger = logging.getLogger("cityfix.ai")


def analyze_civic_issue_image(
    image_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    category_hint: Optional[str] = None
) -> dict:
    """Analyze an image and always return the public CityFix analysis contract."""
    if not image_bytes:
        raise ValueError("Please select an image before starting analysis.")

    _validate_image(image_bytes)

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            import google.generativeai as genai
            from PIL import Image
            import io

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            pil_img = Image.open(io.BytesIO(image_bytes))
            prompt = """
            You are the AI inspection engine for CityFix. Analyze this civic issue image and return ONLY valid JSON:
            {
                "issue_type": "One of: Pothole, Garbage, Broken Streetlight, Overflowing Drain, Road Damage, Water Leakage, Damaged Footpath, Traffic Signal Problem, Other",
                "confidence": 0.95,
                "severity": "One of: LOW, MEDIUM, HIGH, CRITICAL",
                "priority": 85,
                "description": "Brief factual description of the visible issue",
                "recommended_action": "Specific municipal response"
            }
            """
            response = model.generate_content([prompt, pil_img], request_options={"timeout": 20})
            data = _parse_json_response(response.text)
            return _normalize_analysis(data, demo_mode=False, source="Gemini Vision")
        except Exception as e:
            logger.warning("Gemini analysis failed; using demo mode: %s", e)

    return _generate_fallback_civic_analysis(category_hint or filename or "")


def _validate_image(image_bytes: bytes) -> None:
    if len(image_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError(f"Image must be smaller than {settings.MAX_UPLOAD_SIZE_MB} MB.")
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
    except Exception as exc:
        raise ValueError("The uploaded file is not a supported image.") from exc


def _parse_json_response(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("The AI returned an empty response.")
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("The AI response was not a JSON object.")
    return parsed


def _normalize_analysis(data: dict[str, Any], demo_mode: bool, source: str) -> dict:
    supported = {"Pothole", "Garbage", "Broken Streetlight", "Overflowing Drain", "Road Damage", "Water Leakage", "Damaged Footpath", "Traffic Signal Problem", "Other"}
    issue_type = str(data.get("issue_type") or data.get("category") or "Other")
    if issue_type not in supported:
        issue_type = "Other"
    priority = max(0, min(100, int(float(data.get("priority", data.get("priority_score", 50))))))
    severity = str(data.get("severity", "MEDIUM")).upper()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        severity = _severity_for_priority(priority)
    return {
        "issue_type": issue_type,
        "confidence": max(0, min(1, float(data.get("confidence", 0.75)))),
        "severity": severity,
        "priority": priority,
        "priority_level": _severity_for_priority(priority).title(),
        "priority_explanation": _priority_explanation(priority),
        "description": str(data.get("description") or data.get("suggested_description") or "Civic issue identified from the uploaded image."),
        "recommended_action": str(data.get("recommended_action") or "Route this report to the relevant municipal response team for inspection."),
        "demo_mode": demo_mode,
        "analysis_source": source,
    }


def _severity_for_priority(priority: int) -> str:
    if priority <= 25:
        return "LOW"
    if priority <= 50:
        return "MEDIUM"
    if priority <= 75:
        return "HIGH"
    return "CRITICAL"


def _priority_explanation(priority: int) -> str:
    return f"Priority {priority}/100 falls in the {_severity_for_priority(priority).lower()} response band based on visible public-safety and service-impact indicators."


def _generate_fallback_civic_analysis(context: str) -> dict:
    """Intelligent fallback for hackathon demos without active Gemini API keys."""
    context_lower = context.lower()

    if any(k in context_lower for k in ["pothole", "road", "asphalt", "crack", "tar"]):
        return _normalize_analysis({"issue_type": "Pothole", "confidence": 0.93, "priority": 82, "severity": "CRITICAL", "description": "A damaged road surface is visible and may create a collision or tire hazard.", "recommended_action": "Inspect the road and patch or barricade the damaged section."}, True, "Demo mode")
    elif any(k in context_lower for k in ["garbage", "trash", "waste", "dump", "bin"]):
        return _normalize_analysis({"issue_type": "Garbage", "confidence": 0.91, "priority": 68, "severity": "HIGH", "description": "Accumulated waste appears to be spilling into a public area and creating a sanitation concern.", "recommended_action": "Schedule collection and sanitize the affected area."}, True, "Demo mode")
    elif any(k in context_lower for k in ["light", "pole", "lamp", "dark", "electric", "wire"]):
        return _normalize_analysis({"issue_type": "Broken Streetlight", "confidence": 0.88, "priority": 72, "severity": "HIGH", "description": "A streetlight appears damaged or non-functional, reducing visibility for people using the area at night.", "recommended_action": "Dispatch an electrical maintenance crew to inspect and restore the light."}, True, "Demo mode")
    elif any(k in context_lower for k in ["water", "leak", "drain", "flood", "pipe"]):
        return _normalize_analysis({"issue_type": "Water Leakage", "confidence": 0.94, "priority": 88, "severity": "CRITICAL", "description": "Water accumulation suggests a possible pipe or supply-line leak that can weaken the surrounding surface.", "recommended_action": "Send a water utility crew to isolate the leak and secure the area."}, True, "Demo mode")
    else:
        return _normalize_analysis({"issue_type": "Other", "confidence": 0.75, "priority": 50, "severity": "MEDIUM", "description": "A potential civic issue is visible and should be reviewed by a municipal team.", "recommended_action": "Request an in-person inspection and route the report to the appropriate department."}, True, "Demo mode")
