
import json
import re

from langchain_core.prompts import ChatPromptTemplate
from llm.model import get_model


VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an academic evidence verifier.

Assess every claim using only its associated cited passages.

Rules:
1. Evaluate each claim independently.
2. Do not use outside knowledge.
3. Check methods, sample sizes, dates, and findings carefully.
4. Do not confuse a paper's own methods with cited studies.
5. Do not treat a valid citation number as proof of support.
6. Return one assessment for every claim.
7. Return ONLY a valid JSON object with a "results" array.

Each result must contain:
- "id": the claim's integer ID
- "status": "supported", "partially_supported",
  "unsupported", or "unclear"
- "explanation": a short explanation

Use "supported" only if the entire claim is established.
Use "partially_supported" if only part is established.
Use "unsupported" if the evidence does not establish it.
Use "unclear" if the evidence is ambiguous."""
    ),
    (
        "human",
        "Verify these claims:\n{claims_json}"
    )
])


def extract_cited_claims(answer):
    segments = re.split(r"(?<=[.!?])\s+|\n+", answer)

    claims = []

    for segment in segments:
        numbers = re.findall(
            r"\[Source\s+(\d+)\]",
            segment,
            flags=re.IGNORECASE
        )

        if numbers:
            claims.append({
                "claim": segment.strip(),
                "source_numbers": sorted({
                    int(number) for number in numbers
                })
            })

    return claims


def parse_verification_response(content):
    if not isinstance(content, str):
        content = str(content)

    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content.strip()
    ).strip()

    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    return {"results": []}


def verify_answer(answer, documents):
    claims = extract_cited_claims(answer)

    if not claims:
        return []

    allowed_statuses = {
        "supported",
        "partially_supported",
        "unsupported",
        "unclear"
    }

    payload = []
    invalid_claims = {}

    for index, item in enumerate(claims, start=1):
        numbers = item["source_numbers"]

        invalid = [
            number for number in numbers
            if not 1 <= number <= len(documents)
        ]

        if invalid:
            invalid_claims[index] = (
                f"Invalid source references: {invalid}"
            )
            continue

        evidence = []

        for number in numbers:
            doc = documents[number - 1]

            evidence.append({
                "source": number,
                "title": doc.metadata.get("title", "Unknown"),
                "page": doc.metadata.get("page_number"),
                "text": doc.page_content
            })

        payload.append({
            "id": index,
            "claim": item["claim"],
            "evidence": evidence
        })

    assessments = {}

    if payload:
        try:
            response = (
                VERIFICATION_PROMPT | get_model()
            ).invoke({
                "claims_json": json.dumps(
                    payload, ensure_ascii=False
                )
            })

            parsed = parse_verification_response(
                response.content
            )

            for result in parsed.get("results", []):
                if not isinstance(result, dict):
                    continue

                claim_id = result.get("id")

                if type(claim_id) is not int:
                    continue

                if not 1 <= claim_id <= len(claims):
                    continue

                status = result.get("status", "unclear")

                if status not in allowed_statuses:
                    status = "unclear"

                assessments[claim_id] = {
                    "status": status,
                    "explanation": str(
                        result.get("explanation", "")
                    )
                }

        except Exception as error:
            error_message = str(error)
        else:
            error_message = (
                "The verifier did not return an assessment "
                "for this claim."
            )
    else:
        error_message = "No valid claims to verify."

    results = []

    for index, item in enumerate(claims, start=1):
        if index in invalid_claims:
            assessment = {
                "status": "unsupported",
                "explanation": invalid_claims[index]
            }
        else:
            assessment = assessments.get(index, {
                "status": "unclear",
                "explanation": error_message
            })

        results.append({
            **item,
            **assessment
        })

    return results
