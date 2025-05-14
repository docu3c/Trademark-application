# Trademark Analysis Application

A sophisticated trademark analysis system that combines machine learning models and LLM-based analysis to evaluate trademark similarities and potential conflicts.

## Table of Contents
- [Installation](#installation)
- [Requirements](#requirements)
- [Application Overview](#application-overview)
- [Core Components](#core-components)
- [Workflow](#workflow)
- [Usage](#usage)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd trademark-application
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Requirements

The application requires Python 3.8+ and the following key dependencies:
- `streamlit==1.31.1`: Web interface
- `pandas==2.2.0`: Data manipulation
- `PyMuPDF==1.23.8`: PDF processing
- `pydantic==2.6.1`: Data validation
- `python-docx==1.0.1`: Word document generation
- `sentence-transformers`: Semantic similarity analysis
- `phonetics==1.0.5`: Phonetic analysis
- `openai==1.12.0`: LLM integration
- Additional NLP and ML libraries for text processing and analysis

## Application Overview

This application implements a sophisticated trademark analysis system that combines machine learning models with LLM-based analysis to evaluate trademark similarities and potential conflicts. The system processes trademark documents, extracts relevant information, and performs comprehensive similarity analysis.

### Core Components

#### 1. Data Models
- `TrademarkDetails` (BaseModel): Defines the structure for trademark information including:
  - Trademark name
  - Status
  - Serial number
  - International class numbers
  - Owner information
  - Goods/services description
  - Registration details

#### 2. Document Processing
Key functions:
- `read_pdf()`: Extracts text from PDF documents
- `split_text()`: Divides text into manageable chunks
- `extract_trademark_details_code1()` and `extract_trademark_details_code2()`: Extract trademark information from different document formats

#### 3. Similarity Analysis
The system implements a multi-stage analysis pipeline:

##### ML-Based Analysis
- `ml_semantic_match()`: Evaluates semantic similarity between trademarks
- `ml_phonetic_match()`: Assesses phonetic similarity
- Threshold-based filtering:
  - Marks below 0.75 similarity are rejected
  - Marks above 0.85 similarity are automatically accepted
  - Marks between 0.75-0.85 are sent for LLM analysis

##### LLM Analysis
- `analyze_borderline_match()`: Performs detailed analysis of borderline cases
- Uses GPT models to evaluate:
  - Semantic relationships
  - Phonetic similarities
  - Market context
  - Consumer confusion potential

#### 4. Conflict Assessment
- `compare_trademarks()`: Primary comparison function
- `assess_conflict()`: Detailed conflict analysis
- `validate_trademark_relevance()`: Validates similarity findings

#### 5. Opinion Generation
- `generate_trademark_opinion()`: Creates comprehensive analysis reports
- `export_trademark_opinion_to_word()`: Exports results to Word documents
- Includes sections for:
  - Section One Analysis
  - Section Two Analysis
  - Section Three Analysis
  - Web Common Law Analysis

## Workflow

1. **Document Processing**
   - PDF documents are read and processed
   - Text is extracted and normalized
   - Trademark details are parsed and structured

2. **Initial ML Analysis**
   - Semantic similarity check using sentence transformers
   - Phonetic similarity analysis
   - Initial threshold filtering

3. **LLM Analysis**
   - Borderline cases (0.75-0.85 similarity) are analyzed
   - Detailed reasoning and context evaluation
   - Market-specific considerations

4. **Conflict Assessment**
   - Comprehensive comparison of trademarks
   - Goods/services overlap analysis
   - Market context evaluation

5. **Report Generation**
   - Structured opinion generation
   - Word document export
   - Detailed analysis sections

## Usage

1. Start the application:
```bash
streamlit run app_main.py
```

2. Upload trademark documents through the web interface

3. View analysis results and generated reports

## Additional Features

- Crowded field analysis (`analyze_crowded_field()`)
- Component consistency checking (`component_consistency_check()`)
- Web common law analysis
- Comprehensive opinion generation with multiple analysis sections

## Notes

- The system uses a combination of ML models and LLM analysis for optimal results
- Thresholds can be adjusted based on specific requirements
- The application supports multiple document formats and analysis methods 