import json
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger("bq_agent.gemini")


class GeminiService:
    def __init__(self):
        try:
            if settings.GOOGLE_GENAI_USE_VERTEXAI:
                self.client = genai.Client(
                    vertexai=True,
                    project=settings.GOOGLE_CLOUD_PROJECT,
                    location=settings.GOOGLE_CLOUD_LOCATION,
                )
            else:
                self.client = genai.Client()
            self.model_name = settings.GEMINI_MODEL
            logger.info(f"GeminiService initialized with model '{self.model_name}' on Vertex AI")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini Client with Vertex AI settings: {e}. Falling back to default client.")
            try:
                self.client = genai.Client()
                self.model_name = settings.GEMINI_MODEL
            except Exception as e2:
                logger.error(f"Failed to initialize fallback Gemini client: {e2}")
                self.client = None

    def generate_optimization_insights(
        self,
        original_sql: str,
        findings: list,
        bytes_info: Dict[str, Any],
        table_metadata: list
    ) -> Dict[str, Any]:
        """
        Uses Gemini to analyze structured evidence and generate evidence-backed optimization recommendations.
        Strictly prevents hallucination of stats.
        """
        if not self.client:
            return {
                "summary": "Gemini client not initialized. Operating in deterministic rule engine mode.",
                "recommendations": []
            }

        prompt = f"""
You are a Senior Google Cloud BigQuery Performance and Cost Optimization Architect.
Analyze the following SQL query and structured empirical evidence:

Original SQL:
```sql
{original_sql}
```

Structured Findings:
{json.dumps([f.model_dump() if hasattr(f, 'model_dump') else f for f in findings], indent=2)}

Bytes Processed Info:
{json.dumps(bytes_info, indent=2)}

Table Metadata:
{json.dumps(table_metadata, indent=2)}

CRITICAL INSTRUCTIONS:
1. Base all reasoning strictly on the provided empirical evidence, AST findings, and table metadata.
2. DO NOT invent or fabricate BigQuery statistics, byte counts, or slot numbers.
3. If evidence for a metric is unavailable, explicitly state "Insufficient evidence".
4. Output your response as a valid JSON object matching this schema:
{{
  "query_summary": "High-level diagnostic summary of cost/performance posture",
  "recommendations": [
    {{
      "category": "COST|PERFORMANCE",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "finding": "Specific anti-pattern identified",
      "evidence": "Exact clause or metric proving the issue",
      "recommendation": "Clear actionable fix",
      "optimized_sql": "Refactored SQL statement incorporating the fix",
      "expected_impact": "Expected reduction in bytes or slot time",
      "confidence": "HIGH|MEDIUM|LOW"
    }}
  ],
  "refactored_sql": "Complete optimized version of the query"
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini service: {e}")
            return {
                "query_summary": "Rule-engine fallback diagnosis.",
                "recommendations": [],
                "error": str(e)
            }


gemini_service = GeminiService()
