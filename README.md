# Academic Research Assistant

An AI-powered application for organising academic papers, comparing research studies, synthesising literature and identifying potential research gaps.

The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant passages from uploaded PDF documents and generate responses grounded in the selected research papers.

It is built with Python, Streamlit, LangChain, Ollama and Supabase.

## Features

### 1. Literature Research

Upload academic papers in PDF format and save them to a research library.

- Extract text from PDF documents using PyMuPDF.
- Split documents into searchable text chunks.
- Generate vector embeddings using BGE-small-en-v1.5.
- Store document metadata, text chunks and embeddings in Supabase.
- Ask questions about uploaded research papers.
- Retrieve supporting passages and generate evidence-based answers.
- Inspect source references and supporting evidence.

### 2. Literature Comparison

Generate structured comparison matrices for two or more research papers.

The comparison includes:

- Research design
- Dataset
- Sample
- Analytical methods
- Main findings
- Limitations

The application retrieves relevant evidence from each selected paper and uses a local language model to extract comparable information.

Comparison matrices can be exported as CSV files.

### 3. Literature Synthesis

Generate a comparative discussion of selected research papers.

The synthesis examines research designs, datasets, analytical methods, findings and limitations across studies.

Users can provide an optional research topic or question to guide the synthesis.

The application supports author–year attribution when bibliographic metadata is available. Supporting passage references are retained to help users inspect the evidence.

Generated syntheses can be downloaded as Markdown files.

### 4. Research Gap Analysis

Identify potential research gaps within a selected collection of academic papers.

The application examines the supplied literature and distinguishes reported study limitations from possible gaps inferred through comparison.

The analysis can include methodological, empirical, theoretical, data-related and contextual gaps, along with possible research questions.

Identified gaps are preliminary and apply only to the selected papers. They should be checked against a broader literature search before being treated as established research gaps.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Web interface | Streamlit |
| Language model | Qwen3-8B via Ollama |
| LLM framework | LangChain |
| Vector database | Supabase PostgreSQL with pgvector |
| Embedding model | BAAI/bge-small-en-v1.5 |
| Reranking model | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| PDF processing | PyMuPDF |
| Text splitting | RecursiveCharacterTextSplitter |

## System Architecture

The application follows a modular architecture.

**Document processing**

PDF Upload → Text Extraction → Text Cleaning → Chunking → Embedding Generation → Supabase Storage

**Retrieval and question answering**

User Question → Query Embedding → Vector Similarity Search → Cross-Encoder Reranking → Qwen3-8B → Generated Answer

**Literature analysis**

Selected Papers → Evidence Retrieval → Structured Comparison → Literature Synthesis or Research Gap Analysis

The system uses a local language model for generation and Supabase for document storage and vector retrieval.

## Project Structure

```text
academic_research_assistant/
│
├── app.py
├── home_content.py
├── pyproject.toml
├── README.md
│
├── pages/
│   ├── 1_literature_research.py
│   ├── 2_literature_comparison.py
│   ├── 3_research_gap_analysis.py
│   └── 4_literature_synthesis.py
│
├── database/
│   ├── supabase.py
│   └── storage.py
│
├── processing/
│   ├── pdf_parser.py
│   ├── chunking.py
│   └── metadata_extractor.py
│
├── rag/
│   ├── embeddings.py
│   ├── langchain_retriever.py
│   ├── reranker.py
│   ├── qa.py
│   ├── evidence_verifier.py
│   ├── literature_matrix.py
│   ├── literature_synthesis.py
│   └── research_gaps.py
│
└── llm/
    └── model.py
```

The structure lists the main application modules. Additional development, testing and fine-tuning files may be present in the repository.
