# URL Phishing Detection

This project is a **Machine Learning-based system** designed to detect phishing URLs by analyzing their structure and metadata features. It implements a modular and scalable data pipeline that automates data ingestion, validation, transformation, and model training — following best practices for reproducibility and deployment readiness.

---

# Project Overview

Phishing is one of the most common cybersecurity threats on the web. Attackers create fake websites that mimic legitimate services to steal credentials or personal information. This project aims to **automatically classify URLs as legitimate or phishing** using supervised learning techniques.

The pipeline processes a dataset of URLs, extracts key lexical and structural features, trains a model, and exposes the trained model for predictions through a user-facing app.

---

# Core Features

* **Automated data ingestion** from CSV sources
* **Schema validation** of input datasets
* **Data preprocessing and transformation** using `scikit-learn` pipelines
* **Model training and persistence** with pickled artifacts
* **Pre-trained model** available for direct use (`final_model/model.pkl`)
* **Modular architecture** under `networksecurity/`
* **App interface** (`app.py`) for real-time phishing detection
* **MLOps-ready structure** with CI/CD GitHub Actions

---

# Project Architecture

```
url-phishing-detection/
│
├── app.py                    # Web app or prediction interface
├── main.py                   # Entry point to trigger training pipeline
├── push_data.py              # Pushes data to MongoDB or other storage
├── setup.py                  # Package setup script
├── test_mongodb.py           # Connection test for MongoDB
├── requirements.txt          # Python dependencies
│
├── Network_Data/
│   └── phisingData.csv       # Training dataset
│
├── data_schema/
│   └── schema.yaml           # Defines data schema for validation
│
├── final_model/
│   ├── model.pkl             # Trained classification model
│   └── preprocessor.pkl      # Preprocessing pipeline
│
└── networksecurity/
    ├── components/           # Modular pipeline components
    │   ├── data_ingestion.py
    │   ├── data_transformation.py
    │   ├── data_validation.py
    │   └── model_trainer.py
    │
    ├── constant/             # Global constants and configuration
    │   └── training_pipeline/
    │       └── __init__.py
    │
    ├── cloud/                # Placeholder for cloud-related utilities
    └── entity/               # Entity definitions and configs
```

---

# Machine Learning Pipeline

## 1️⃣ Data Ingestion

Loads the dataset (`Network_Data/phisingData.csv`) and splits it into training and testing subsets. Implements error handling and logging for traceability.

## 2️⃣ Data Validation

Checks the dataset against the schema defined in `data_schema/schema.yaml`. Ensures column names, datatypes, and expected structure match before proceeding.

## 3️⃣ Data Transformation

Applies preprocessing transformations such as:

* label encoding / one-hot encoding
* handling missing values
* feature scaling and normalization

The pipeline object is serialized into `final_model/preprocessor.pkl`.

## 4️⃣ Model Training

Trains a classification model (e.g., RandomForest, XGBoost, or Logistic Regression). The trained model is serialized as `final_model/model.pkl` for prediction use.

## 5️⃣ Prediction & App Interface

The `app.py` file provides an interface (possibly Flask/Streamlit) for predicting whether a given URL is **phishing** or **legitimate**.

---

# Installation

## Prerequisites

Ensure you have the following installed:

* Python 3.8 or above
* pip package manager

## Setup Steps

```bash
# Clone the repository
git clone https://github.com/dattatejaofficial/url-phishing-detection.git
cd url-phishing-detection

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows

# Install dependencies
pip install -r requirements.txt
```

---

# Running the Project

## Train the Model

```bash
python main.py
```

This will trigger the end-to-end data ingestion, validation, transformation, and model training pipeline.

## Run the Application

```bash
python app.py
```

This launches the web interface (if implemented in Flask/Streamlit) to test URLs for phishing detection.

---

# Deployment

The project is structured to support deployment on **cloud platforms** like AWS, Azure, or Heroku. CI/CD integration is set up using **GitHub Actions** (`.github/workflows/main.yml`).

You can also containerize the app using **Docker** by creating a `Dockerfile` and deploying it to services like **AWS ECS**, **Google Cloud Run**, or **Heroku**.

---

# Tech Stack

| Category   | Technology                                            |
| ---------- | ----------------------------------------------------- |
| Language   | Python 3.8+                                           |
| Libraries  | scikit-learn, pandas, numpy, Flask/Streamlit, pymongo |
| Storage    | MongoDB (for data persistence)                        |
| ML Tools   | Pickle, scikit-learn Pipelines                        |
| Deployment | GitHub Actions, Docker (optional)                     |

---

# Folder Highlights

| Folder                       | Description                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| `networksecurity/components` | Core machine learning modules (data ingestion, transformation, validation, training) |
| `final_model/`               | Serialized pre-trained models                                                        |
| `Network_Data/`              | Raw CSV dataset                                                                      |
| `data_schema/`               | YAML schema for data validation                                                      |
| `cloud/`                     | Placeholder for cloud integration utilities                                          |
| `constant/`                  | Constants used across the project                                                    |

---

# 📊 Dataset

The dataset used for this project is stored at:

```
Network_Data/phisingData.csv
```

It contains features extracted from URLs such as length, number of dots, presence of special characters, and other lexical indicators commonly used for phishing detection.

---

# Author

**Datta Teja**
<br/>
*Data Scientist & Machine Learning Engineer*
[GitHub Profile](https://github.com/dattatejaofficial)

---

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

# Acknowledgements

* [UCI ML Repository - Phishing Websites Dataset](https://archive.ics.uci.edu/ml/datasets/phishing+websites)
* Open-source Python community for continuous contributions

---
