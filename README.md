# Phishing URL Detection System

> An end-to-end Machine Learning System that detects Phishing URLs in real time - from raw data ingestion to a deployed browser extension - achieving **98.28% Accuracy, 97.75% Precision, 97.25% Recall** with an XGBoost classifier

---

## Project Overview

Phishing attacks are one of the most prevelant cyber security threats, tricking users into visiting malicious websites disguised as legitimate ones. This project builds a **Production-Ready Phishing URL Detection System** that:

- Classifies any URL as **Legitimate** or **Phishing** using purely structural & statistical URL features (no webpage content is required)
- Exposes predictions through a **REST API** (FastAPI + Uvicorn)
- Integrates with **PhishGuard** - a browser extension to provide a real-time detection
- Is containerized with **Docker** and experiment-tracked with **MLFlow**

This project demonstrates the full Data Science lifecycle - data collection, feature engineering, EDA, model training, evaluation, explainability, deployment, monitoring, and model retraining.

---

## System Architecture (Production Pipeline)
This system is built as a closed-loop **Machine Learning Pipeline** that continuously adapts using real-world feedback.

<p align="center">
  <img src="images/System_Architecture.png" width="850"><br>
  <em>System Architecture & Inference of Phishing Detection Pipeline</em>
</p>  

### Training Pipeline

**Workflow:**

Raw Data → Data Preparation → Feature Extraction → Data Validation → Data Persistance → Data Transformation → Model Training → Model Evaluation → Model Finalization → Artifact Publishing

**Responsibilities**
- Cleans malformed and adversarial URLs
- Expands shortened URLs before feature extraction
- Extracts ~30 structured features
- Trains XGBoost with Bayesian Optimization
- Applies threshold optimization for real-world performance

### Monitoring System

Runs as a serverless Azure Function

- Collects recent feedback data from MongoDB
- Compares with training data distribution
-Detects:
    - Feature drift using **Population Stability Index (PSI)**
    - Data volume changes

**Key Design:**
- Uses a **rolling 15-day window**
- Executes only when required (cost-efficient)
- Stores reports in **Azure Blob Storage**

### Automated Retraining Pipeline
Triggered when monitoring detects significant change.

**Trigger Conditions:**
- Feature drift exceeds threshold
- OR sufficient new data is available

**Workflow:**
Monitoring → Decision Engine → GitHub Actions → Retraining Pipeline

**Retraining Pipeline:**
- Merges historical + feedback data
- Applies **sample weighting (recent data prioritized)**
- Retries model
- Compares with production model
- Promotes only if performance improves

---

## Feedback Loop
1. User interacts with browser extension
2. Feedback stored in MongoDB
3. Monitoring detects distributions changes
4. Retraining pipeline updates the model

**→** This enables continuous adaptation to evolving phishing strategies

## Dataset


| Property | Details |
|---|---|
| Total URLs | ~253,000 (cleaned to ~201,000 after deduplication) |
| Classes | Phishing (`1`), Legitimate (`0`) |
| Class Balance | Near-equal distribution |
| Features Used | 30 numerical features |
| Features Excluded | Hexadecimal features (low discriminatory power via SHAP) |

---

Feature Engineering

Features were extracted purely from the URL string, organized into **8 groups**:

| Group | Features |
|---|---|
| **URL Components** | Protocol, Domain, Subdomain, TLD, SLD, Path, Query |
| **Length-based** | URL length, domain length, path length, query length, URL depth, subdomain count |
| **Domain Features** | TLD length, IPv4 usage, port presence |
| **SLD Features** | SLD length, digit/hyphen presence, token count |
| **Character-level** | Dot, hyphen, underscore, slash, digit, alphabet, special character counts |
| **Entropy Features** | URL entropy, path entropy, domain entropy, SLD entropy |
| **Token-based** | Domain tokens, path tokens, total tokens, average token length |
| **Hex Features** | Hex character presence, count, ratio *(excluded post-SHAP analysis)* |

---

## Key EDA Findings

- **Protocol:** Three protocols observed - HTTPS, HTTP, and FTP. Legitimate URLs are predominantly use HTTPS. Phishing URLs are split across HTTP and HTTPS, showing attackers increasingly adopt HTTPS to appear trustworthy. FTP URLs are extremely rare and appear only in phishing samples, suggesting misuse for malicious payload delivery.

- **URL Length:** Phishing URLs have significantly longer and more right-skewed distributions for URL, path, and query lengths - complex structures used to evade detection. URL length inflates primarily due to path and query length, not domain length.

- **Subdomains & Depth:** Phishing URLs exhibit deeper directory structures and more multi-level subdomains, mimicking legitimate hierarchical domains.

- **TLDs & SLDs:** Phishing URLs favor low-cost TLDs (`.top`, `.icu`, `.dev`, `.app`); legitimate URLs cluster under `.org` and `.edu`. Phishing SLDs contain more hyphens and digits, indicating manipulation to resemble brand names.

- **Entropy:** Path entropy is notably higher for phishing URLs, indicating greater randomness and obfuscation in path construction.

- **Null Values:** Null TLD values occur in IP-based URLs (no domain to extract from); null SLD values reflect intentionally malformed URLs — both are structural by design, not data collection errors.

- **Hex Features:** Found to be statistically indistinguishable between classes — excluded from final model training.

---

## Model Training & Results

Two classifiers were trained and evaluated:


| Model | Accuracy | Precision | Recall | F1-Score |
|---|---|---|---|---|
| Random Forest | ~97.75% | ~98.67% | ~96.69% | ~97.05% |
| **XGBoost** | **~98.28%** | **~99.36%** | **~97.05%** | **~98.21%** |

**XGBoost** was selected as the final model due to superior generalization performance.


### Data Preprocessing
Before training, the following preprocessing steps were applied:
- **Null handling:** Numerical features derived from missing URL components (e.g., no TLD in IP-based URLs) were set to `0`; categorical components were excluded from modelling.
- **Feature encoding:** Boolean signals (`has_https`, `url_has_ipv4`, `url_has_port`) were converted to integer indicators.
- **Deduplication:** Removed **33,312 duplicate rows**, reducing the dataset from 253,051 to ~201,000 rows.
- **Final feature set:** 30 numerical features across 7 groups (hexadecimal features excluded after EDA).


### Optimization Steps
- **Hyperparameter Tuning:** Used `hyperopt` with cross-validation for Bayesian optimization — improved Phishing detection recall from 96% → 97.25% using
- **Threshold Optimization:** Final decision threshold set to ≥ 0.45 with a recall constraint of ≥ 0.9725. Result: recall of 0.9734, precision of 0.9904, F1-score of 0.9821, overall accuracy of 98% — with no meaningful trade-off in model quality.
- **SHAP Analysis:** Identified the 8 most influential features — HTTPS presence, dot count in domain, domain entropy, SLD length, path length, URL depth, digit count, and path entropy. Eliminated 4 low-impact features (`total_tokens`, `sld_token_count`, `url_has_ipv4`, `url_has_port`).


## Deployment
 
The trained model is deployed as a real-time system with two interfaces:
 
**1. REST API (FastAPI)**
- Accepts a URL as input and returns a prediction (`phishing` or `legitimate`) with confidence score
- Served with `Uvicorn` for async, high-performance inference
- Containerized with **Docker** for portability

**2. Browser Extension**
- Intercepts URLs as the user browses
- Calls the FastAPI backend in real time
- Automatically alerts or blocks phishing URLs

**3. Experiment Tracking & Monitoring**
- **MLflow** for model versioning, parameter logging, and metric tracking
- **Azure Blob Storage** for artifact storage
- **MongoDB** for storing prediction logs
- **Azure Functions for scheduling**
- **Volume-based** retraining trigger
---

## Technological Stack
| Category | Tools |
|---|---|
| **Language** | Python |
| **Data Processing** | Pandas, Numpy, tldextract, aiohttp |
| **Visualization** | Matplotlib, Seaborn |
| **ML / Modeling** | scikit-learn, XGBoost, hyperopt |
| **Explainability** | SHAP |
| **API / Serving** | FastAPI, Uvicorn |
| **Experiment Tracking** | MLflow |
| **Monitoring** | Azure Functions |
| **Containerization** | Docker |
| **Storage** | MongoDB, Azure Blob Storage |
| **Extension** | JavaScript, HTML, CSS |
| **Notebooks** | Jupyter |

---

## Repository Structure
 
```
url-phishing-detection/
├── notebooks/              # Jupyter notebooks: EDA, feature engineering, model training
├── app/                    # FastAPI application (REST API)
├── extension/              # Browser extension source (JS, HTML, CSS)
├── phishingdata/           # Raw and processed datasets
├── phishingsystem/         # Core ML pipeline modules
├── data_schema/            # Feature schema definitions
├── scripts/                # Utility and automation scripts
├── .github/workflows/      # CI/CD pipelines
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── setup.py                # Package setup
└── Phishing URL Detection Report.md  # Detailed project report
```

---

## Setup & Installation
 
```bash
# Clone the repository
git clone https://github.com/dattatejaofficial/url-phishing-detection.git
cd url-phishing-detection
 
# Install dependencies
pip install -r requirements.txt
 
# Run the API server
uvicorn app.app:app --reload
 
# Run with Docker
docker build -t phishing-detection .
docker run -p 8000:8000 phishing-detection
```
 
---

## Results Summary
 
- **98.28% test accuracy** on ~201K URLs
- **99.36% precision** — very few legitimate URLs flagged as phishing
- **97.34% recall** after threshold optimization — catches the vast majority of phishing attempts
- **Real-time inference** via browser extension + REST API
- **Fully containerized and monitored** production pipeline

---

## System Performance

- Average Latency: ~**39 ms**
- Median Latency: ~**32 ms**
- P95 Latency: ~**90 ms**
- P99 Latency: ~**120 ms**
- Peak Throughtput: ~**45 requests/sec** (at ~100 concurrent users)
- Failure Rate: 0%

Observed occasional latency spikes up to ~**370 ms** under load, indicating potential optimization in request handling and model inference.

---

## Engineering Challenges & Solutions
 
Building this system end-to-end involved solving several real-world engineering problems that go beyond standard ML tutorials.
 
---

### Challenge 1 — Invisible Unicode Characters Breaking CSV Storage
 
**Problem:** Phishing URLs frequently contain invisible Unicode characters (zero-width spaces, control characters, etc.) as part of adversarial construction. Even after applying cleaning routines, some of these characters persisted silently in the data. When the cleaned URLs were saved to `.csv` files and later read back, pandas failed to parse them correctly — causing rows to be skipped, fields to be misread, or files to be entirely unreadable.
 
**Solution:** Switched all intermediate and processed data storage from `.csv` to **Apache Parquet format**. Unlike CSV, which is a plain-text format sensitive to encoding ambiguity, Parquet is a binary columnar format with strict, standardized type encoding. It stores strings as binary with explicit byte boundaries, which means embedded invisible characters are preserved exactly as-is without breaking the file structure. This also had the side benefit of reducing storage size and speeding up read/write operations significantly.

---

### Challenge 2 — Cost-Efficient Scheduled Monitoring Without a Persistent VM
 
**Problem:** The system needed a scheduled job to run drift detection and model performance monitoring (via Evidently) on fresh URL data. Apache Airflow is the industry-standard tool for this, but it requires a **continuously running Virtual Machine** — meaning the VM incurs compute costs 24/7, even when the monitoring job only runs briefly. For a project optimizing for cloud cost, this was unacceptable.
 
**Solution:** Replaced Airflow with **Azure Functions on the Consumption Plan** using a timer trigger. The function is scheduled via a CRON expression to fire **twice a month** (e.g., on the 1st and 15th of each month). With Azure's serverless model, compute is billed only for the duration the function actually executes — there is no idle cost between runs. This delivers the same scheduled orchestration capability as Airflow at a fraction of the cost, with no infrastructure to manage.
 
> CRON expression used: `0 0 0 1 15 * *` — triggers at midnight on the 1st and 15th of every month.

---

### Challenge 3 — Handling URL Shorteners During Feature Extraction
 
**Problem:** A meaningful portion of phishing URLs in the dataset were **wrapped behind URL shorteners** (e.g., `bit.ly`, `tinyurl.com`, `t.co`). Extracting structural features (domain, path depth, entropy, etc.) from the shortener URL itself is meaningless — the real malicious URL is hidden behind the redirect. Simply ignoring these URLs would introduce blind spots in the model.
 
**Solution:** Built a **two-stage URL resolution pipeline**:
1. A curated list of known URL shortener domains is maintained in a local **SQLite database**.
2. Before feature extraction, each URL's domain is checked against this list. If a match is found, the `requests` library follows the redirect chain to **unwrap the full destination URL**, which is then passed to the feature extractor. Non-shortened URLs skip this step and proceed directly to extraction.
This ensures the model always operates on the true underlying URL, not the obfuscated shortener wrapper. The SQLite lookup makes the check fast and avoids repeated network overhead for known non-shorteners.

---

## Skills Demonstrated
 
- End-to-end ML pipeline design and implementation
- Large-scale data cleaning, feature engineering, and EDA
- Binary classification with ensemble methods (Random Forest, XGBoost)
- Model interpretability with SHAP
- Bayesian hyperparameter optimization with hyperopt
- MLOps: experiment tracking (MLflow), drift monitoring (Evidently), Docker deployment
- API development with FastAPI
- Browser extension development for real-world integration
- Serverless cloud architecture (Azure Functions) for cost-optimized scheduling
- Robust data storage design using Parquet for encoding-safe persistence
- URL resolution pipeline with SQLite-backed shortener detection

---

## Limitations
- Does not analyze webpage content (HTML, JS)
- Cannot detect phishing using compromised legitimate domains
- Vulnerable to adversarial URL crafting with clean structure