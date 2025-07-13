# 🏥 AutoClinicAI System - Team Tiger

A comprehensive medical AI system that processes patient symptoms, analyzes medical images, and provides evidence-based treatment recommendations through a coordinated workflow of specialized agents.

## 🚀 Overview

This system uses a multi-agent architecture to provide comprehensive medical analysis, from initial symptom triage to final treatment recommendations. Each agent specializes in a specific aspect of medical assessment, working together under the coordination of a Master Agent.

## 🤖 Agent Architecture

### Master Agent
- **Role**: Orchestrates the entire medical workflow
- **Function**: Coordinates between specialized agents and manages data flow
- **Technology**: Automatically selects and calls appropriate agents based on context

### Specialized Agents

#### 1. 🔍 Analyzer Agent
- **Purpose**: Extract structured triage information from patient descriptions
- **Input**: Free-text patient symptoms and medical history
- **Output**: Structured JSON with patient's basic information, symptoms, severity, and triage level

#### 2. 📸 Image Upload MCP Agent
- **Purpose**: Process and upload medical images for AI analysis
- **Input**: Medical image file ID (X-rays, CT scans, etc.)
- **Output**: Uploaded image URI ready for analysis

#### 3. 📄 OCR Lab Test Reader
- **Purpose**: Read and analyze blood test result to identify abnormal values
- **Input**: PDF file of the blood test result
- **Output**: Analysis of the blood test result (abnormal values outside of the normal range)

#### 4. 🧠 Diagnosis Reasoner Agent
- **Purpose**: Generate differential diagnoses based on symptoms and lab test analysis result
- **Input**: Structured petient information and lab test analysis result
- **Output**: 1-3 likely diagnoses with medical justifications

#### 5. 📚 PubMed Search Agent
- **Purpose**: Research current medical literature for treatment protocols
- **Input**: Likely diagnosis for patient's problem
- **Output**: Evidence-based treatment research summary

#### 6. 💊 Treatment Recommender Agent
- **Purpose**: Generate comprehensive treatment plans
- **Input**: Diagnosis data and research findings
- **Output**: Complete treatment recommendations

### MCP Server
#### 1. 📸 Medical Image Analysis MCP
- **Purpose**: Analysis the lab medical image of patient (X-rays, CT scans, etc.)
- **Input**: Medical Image
- **Output**: Analysis from the medical images 


## 🔄 Example Workflow Process

[put image later]


## 🛠️ Technical Requirements

### Prerequisites
- Python 3.12+
- UV package manager
- OpenAI API access
- PubMed API access
- MCP server setup

### Environment Variables
```bash
# Required API Keys
OPENAPI_KEY=your_openai_api_key
PUBMED_EMAIL=your_email@domain.com

# Other configurations
MCP_ENDPOINT=https://your-mcp-server.com
```

## 📊 Agent Specifications

| Agent | Input Format | Output Format | Processing Time |
|-------|-------------|---------------|-----------------|
| Analyzer | Free text | JSON structure | ~2-3 seconds |
| Image Upload MCP | File ID | Upload URI | ~5-10 seconds |
| Diagnosis Reasoner | JSON + Image data | Diagnosis list | ~10-15 seconds |
| PubMed Search | Search terms | Research summary | ~5-8 seconds |
| Treatment Recommender | Diagnosis + Research | Treatment plan | ~8-12 seconds |

## 🎯 Example Usage
### 🩺 Case 1: Mr. Adam Nguyen – Respiratory Symptoms with Chest X-ray
📝 Prompt:

Please analyze this patient's information, upload the chest X-ray to MCP, then use MCP to analyze the image. With all of the details gathered, suggest likely diagnoses, provide insights from relevant publications in PubMed, and recommend a final treatment plan.

Patient Information:
"My name is Adam Nguyen. I'm a 45-year-old male. I've been a smoker for over 20 years. Lately, I've been experiencing a persistent dry cough, some shortness of breath when climbing stairs, and mild chest discomfort. These symptoms started around 7 days ago and have gradually worsened. I haven't had a fever. I had a chest X-ray done earlier today and have uploaded it for review."

📎 Uploaded File:
case1_chest-xray.jpeg

### 💉 Case 2: Ms. Linh Tran – Fatigue & Diabetes-Related Symptoms
📝 Prompt:

Please analyze this patient's information, read the blood test to identify anomalies. With all of the details gathered, suggest likely diagnoses, provide insights from relevant publications in PubMed, and recommend a final treatment plan.

Patient Information:
"Hi, I’m Linh Tran. I’m a 32-year-old female. For the past few weeks I’ve been feeling very tired all the time, even after sleeping well. I also get dizzy when I stand up quickly, and my skin feels dry and itchy lately. I’ve been more thirsty than usual and sometimes need to urinate frequently. I recently had a blood test done and I’ve uploaded the report."

📎 Uploaded File:
case2_blood_test_report.pdf

## ⚠️ Medical Disclaimer

All medical recommendations should be reviewed by qualified healthcare professionals. This system does not replace professional medical advice, diagnosis, or treatment.