# Executive Cost Estimation & Infrastructure Financial Model
## PMC Grievance Intelligence & Officer Query System

**Document Version:** 1.0  
**Target Audience:** Municipal Commissioner, HODs, IT Department, Procurement & Finance Committee  
**LLM Architecture:** OpenRouter API routing to Open-Source Enterprise Models  

---

## 1. Executive Summary

The Pune Municipal Corporation (PMC) Grievance Intelligence & Officer Query System is engineered to process municipal officer natural language queries, dynamically inspect live PostgreSQL data schema, execute deterministic SQL queries, and synthesize executive decision reports.

To comply with **PMC Data Security Mandates**, the system routes queries exclusively through **Open-Source / Open-Weight Enterprise LLM models** via OpenRouter. This document outlines the unit economics, token consumption metrics, projected operational costs (in USD and INR), and a financial comparison against proprietary LLMs and on-premise hardware infrastructure.

---

## 2. LLM Provider & Open-Source Model Rate Sheet

All models configured in the primary LLM client (`backend/app/api/llm_client.py`) carry **free commercial production licenses** (Apache 2.0, MIT, Llama Community) and are hosted on serverless infrastructure via OpenRouter.

| Model Identifier | Provider / Developer | Open-Source License | Input Rate (Per 1M Tokens) | Output Rate (Per 1M Tokens) |
| :--- | :--- | :--- | :---: | :---: |
| `meta-llama/llama-3.3-70b-instruct` *(Primary)* | Meta AI | Llama 3.3 Community License | **$0.12 USD** | **$0.30 USD** |
| `qwen/qwen-2.5-coder-32b-instruct` *(Fallback)* | Alibaba Cloud | Apache 2.0 Commercial | **$0.07 USD** | **$0.16 USD** |
| `deepseek/deepseek-r1-distill-llama-70b` *(Reasoning)* | DeepSeek AI | MIT License | **$0.23 USD** | **$0.69 USD** |
| `meta-llama/llama-3.1-8b-instruct` *(Fast)* | Meta AI | Llama 3.1 Community License | **$0.05 USD** | **$0.08 USD** |

---

## 3. Token Consumption & Unit Query Cost Model

### 3.1 Per-Query Token Footprint Analysis

1. **Input Context Footprint (~1,500 Tokens):**
   * Dynamic Database Schema & Column Data Types (`dynamic_schema.py`): ~900 tokens
   * Live Sample Value Introspection (`ward_name`, `user_type`, `status_name`): ~300 tokens
   * Conversation History + Current Officer Question: ~300 tokens
2. **Output Footprint (~500 Tokens):**
   * Generated PostgreSQL `SELECT` Block: ~100 tokens
   * Synthesized Executive Markdown Report & Key Metrics Table: ~400 tokens

### 3.2 Unit Query Cost Calculation (`llama-3.3-70b-instruct`)

$$\text{Input Cost} = 1,500 \text{ tokens} \times \frac{\$0.12}{1,000,000} = \$0.00018\text{ USD}$$

$$\text{Output Cost} = 500 \text{ tokens} \times \frac{\$0.30}{1,000,000} = \$0.00015\text{ USD}$$

$$\mathbf{\text{Total Unit Cost Per Query}} = \$0.00018 + \$0.00015 = \mathbf{\$0.00033\text{ USD}}$$

> **Unit Cost Conversion:**  
> **$0.00033 USD** $\approx$ **0.033 Cents (USD)** $\approx$ **₹0.027 INR** per officer query.

---

## 4. Projected Monthly Operational Cost Tiers

Below are projected monthly operating expenses across three PMC deployment scales:

| Scale Tier | Target Operational Scope | Daily Queries | Monthly Queries | Est. Monthly Cost (USD) | Est. Monthly Cost (INR) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Tier 1: POC / Pilot** | Testing & Executive Review | 100 queries/day | 3,000 queries | **~$1.00 USD** | **~₹83 INR** |
| **Tier 2: Ward Officers** | 16 Ward Offices & HODs | 1,000 queries/day | 30,000 queries | **~$10.00 USD** | **~₹830 INR** |
| **Tier 3: Enterprise PMC** | Full Municipal Officer Rollout | 10,000 queries/day | 300,000 queries | **~$100.00 USD** | **~₹8,300 INR** |

---

## 5. Architectural Financial Comparison

### 5.1 OpenRouter Open-Source vs. Proprietary Closed LLMs (e.g. GPT-4o)

* **Proprietary Closed LLM (GPT-4o):** ~$2.50 / $10.00 per 1M tokens.  
  *Cost per 300,000 monthly queries:* **~$1,875 USD (~₹1,55,000 INR)**.
* **OpenRouter Open-Source Stack (Llama 3.3 70B):** $0.12 / $0.30 per 1M tokens.  
  *Cost per 300,000 monthly queries:* **~$100 USD (~₹8,300 INR)**.
* **Financial Savings:** **94.6% Cost Reduction** while maintaining full open-source data security compliance.

### 5.2 OpenRouter Serverless vs. On-Premise GPU Server Hosting

* **On-Premise GPU Infrastructure:**  
  Running Llama 3.3 70B locally requires 2x NVIDIA A100 (80GB) or H100 GPU servers (~$25,000+ upfront hardware cost, plus high electricity, cooling, and maintenance overhead).
* **OpenRouter Serverless API:**  
  Zero upfront hardware investment. Pay strictly per-query token consumption with automatic high-speed cloud autoscaling.

---

## 6. Financial Governance & Cost Management Recommendations

1. **API Key Budget Hard Limit:** Set an automated spending hard limit on OpenRouter (e.g., $20.00 USD/month for Pilot phase).
2. **Schema Cache TTL Optimization:** The system caches dynamic database schema for 60 seconds (`CACHE_TTL_SECONDS = 60`), preventing unnecessary schema re-fetching during rapid multi-turn chats.
3. **Response Auto-Truncation:** SQL queries enforce `LIMIT 50` on data previews to keep output token sizes compact and fast.
