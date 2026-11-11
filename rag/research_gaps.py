
from langchain_core.prompts import ChatPromptTemplate

from llm.model import get_model
from rag.literature_synthesis import build_paper_context


# ==========================================
# RESEARCH GAP ANALYSIS PROMPT
# ==========================================

GAP_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an academic research gap analysis assistant.

Identify potential research gaps within the selected
collection of academic papers.

Rules:
1. Use only the supplied research papers and evidence.
2. Focus on the user's research topic or question.
3. Distinguish reported limitations from inferred gaps.
4. Do not invent findings, methods or citations.
5. Do not claim a gap exists across the entire field.
6. Missing information in retrieved passages does not
   prove that a paper has not addressed the topic.
7. Do not treat unrelated studies as conflicting evidence.
8. Cite supporting passages using references such as
   [Paper 1, Source 2].
9. Preserve uncertainty.
10. Suggest research questions only when supported
    by the available evidence.

For each candidate gap, use this structure:

### Gap N: Descriptive title

**Category:** Methodological, empirical, theoretical,
data-related, contextual or unresolved findings.

**Evidence from selected studies:**
Explain what the studies actually examine.

**Potential gap:**
Explain what remains insufficiently addressed
within the selected literature.

**Suggested research question:**
Provide a specific researchable question.

**Further verification needed:**
Explain what additional literature should be checked.

Identify no more than four candidate gaps.

If the evidence is insufficient, state this instead
of inventing research gaps.

Finish with a short statement explaining that
the analysis is limited to the selected papers."""
    ),
    (
        "human",
        """Research topic:
{topic}

Selected literature and supporting evidence:
{context}

Identify potential research gaps."""
    )
])


# ==========================================
# GENERATE RESEARCH GAPS
# ==========================================

def generate_research_gaps(
    rows,
    evidence_by_paper,
    paper_ids,
    topic
):

    if not topic or not topic.strip():
        raise ValueError(
            "A research topic or question is required."
        )

    context = build_paper_context(
        rows=rows,
        evidence_by_paper=evidence_by_paper,
        paper_ids=paper_ids
    )

    model = get_model()

    chain = GAP_PROMPT | model

    response = chain.invoke({
        "topic": topic.strip(),
        "context": context
    })

    return str(response.content)
