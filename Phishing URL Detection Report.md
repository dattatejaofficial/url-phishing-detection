# Phishing URL Detection using Machine Learning
A Machine Learning-based system to detect phishing URLs using structural and statistical URL features.<br>
The system is designed for high accuracy, low latency and suitability for real-time applications such as browser extensions or security APIs.

## Problem Statement
Phishing URLs are crafted to closely resemble legitimate URLs while redirecting users to malicious websites. Traditional rule-based systems struggle to detect phishing patterns.

Goal:
Build a robust Machine Learning model that can accurately classify URLs as:
- Phishing
- Legitimate

using only URL-based features, without relying on webpage content.

## 1. Data Preparation

### Dataset Description
- Total URLs: ~2,53,000 (later reduced to ~2,01,000)
- Classes: Phishing, Legitimate
- Balance: Nearly equal distribution between classes

### Key Observations from Raw URLs
- Phishing URLs often:
  - Use **HTTP** (but many also use HTTPS)
  - Contains **IP addresses** instead of domains
  - Have very **long paths** & **query** strings
  - Embed **random strings** & **hexadecimal characters**
  - Use **URL shorteners** & **free hosting services**

### URL Cleaning & Validation
- Removed:
  - Zero-width & invisible Unicode characters
  - Control characters
  - Malformed protocol syntax
  - Trailing slashes
- Validating URLs using Regex patterns
- Expanded working shortened URLs using async and caching

### Feature Extraction
Extracted features were grouped into 8 categories:

**1. URL Components**
- Protocol, Domain, Subdomain, TLD, SLD, Path & Query

**2. Length-based Features**
- URL Length, Domain Length, Path Length, Query Length
- URL Depth, Subdomain count

**3. Domain Features**
- TLD Length, IPv4 usage, Port presence

**4. SLD Features**
- Length, digit presence, hyphen presence, token count

**5. Character Features**
- Dot, hyphen, underscore, slash, digit, alphabet, special-character counts

**6. Entropy Features**
- URL Entropy, Path Entropy, Domain Entropy, SLD Entropy

**7. Token-based Features**
- Domain tokens, Path tokens, Total tokens, avg. token length

**8. Hexadecimal Features**
- Presence, count, ratio of hexadecimal characters

Each feature group was saved as a separate CSV for modular analysis.

## 2. Exploratory Data Analysis (EDA): Key findings

### Data Quality & Missing values
- The URL components, domain features, & SLD features dataframes contain null values primarily due to missing URL components or failed parsing.
- URLs that use IP addresses instead of domain names naturally produce null TLD values.
- Intentionally malformed URLs result in null SLD values, reflecting adversarial URL construction startegies.
- Null values are threshold structural in nature & not a result of data collection errors.

### Dataset Distribution & Protocol usage
- The dataset is balanced, containing roughly equal number of phishing & legitimate URLs, reducing classification bias.
- Three URL Protocols are observed: https, http, ftp
- Legitimate **URLs predominantly use HTTPS**, reflecting standard security packages.
- Phishing URLs are split between HTTP & HTTPS, indicating attackers increasingly adopt HTTPS to appear trustworthy.
- FTP URLs are extreamely rare & occur only in phishing URLs, suggesting misuse for malicious payload delivery.

### URL Component Presence Analysis
- Phishing URLs have more missing subdomains compared to legitimate URLs.
- Null TLD values are extremely rare in both phishing & legititmate URLs.
- Both classes predominantly contain non-null paths, indicating that path presence alone is not a distinguishing feature.
- Phishing URLs contain more null queries.

### TLD & SLD Usage Patterns
- Phishing URLs strongly favour low-cost TLDs such as:
  - `.com`, `.net`, `.top`, `.icu`, `.dev`, `.app`
- Legitimate URLs appear more frequently under reputable TLDs such as:
  - `.org`, `.edu`
- Phishing URLs frequently rely on URL shorteners, as indicated by SLDs such as:
  - `bit.ly`, `qrco`

### Length-based Structural Characteristics
- Phishing URLs exhibit longer & more right-skewed distributions for:
  - URL Length
  - Path Length
  - Query Length
- This indicates longer & complex URL structures, often used to evade detection.
- Phishing domains tend to be either unusually short or unusually long, unlike legitimate domains, which are more consistently structured.
- URL length increases primarily  due to path length and query length, rather than domain length.

### Depth & Subdomain Analysis
- Phishing URLs exhibit deeper directory structure, with more path levels than legitimate URLs.
- Multi-level subdomains are more common in phishing URLs, reflecting attempts to mimic legitimate hierarchical domains.

### Domain & Network-Level Indicators
- Greater variation in TLD Length is observed in phishing URLs compared to legitimate ones.
- IPv4-based URLs are rare in both classes but appear slightly more often in phishing URLs, suggesting attempts to bypass domain-based trust mechanisms.
- Non-standard port numbers are used slightly more often in phishing URLs but remain rare overall.

### SLD Structural Properties
- SLD Length distributions are nearly identical for phishing & legitimate URLs, offering little discriminatory power.
- Phishing SLDs contain more hyphens & digits, indicating manipulation to resemble brand names or generate random-looking domains.
- Slightly higher SLD token counts are observed in phishing URLs, suggesting attackers split domain names into multiple segments to appear legitimate.

### Character-Level & Entropy Analysis
- Phishing URLs show:
  - Higher dot counts
  - More slashes
  - Deeper directory structures
  - Increased digit usage
  - More special characters
- Path entropy varies significantly and is higher for phishing URLs, indicating greater randomness & obfuscation.
- URL Entropy & Domain Entropy also show more spread for phishing URLs, though with less variation than path entropy.

### Hexadecimal Feature Analysis
- Hexadecimal character presence, count and ratio appear almost identical in both phishing & legitimate URLs.
- These features do not provide meaningful discrimation & were therefore excluded from final model training.

## 3. Data Preprocessing

### Handling Missing Values
- Null values occur mainly due to:
  - IP-based URLs (no TLD/SLD)
  - Intentionally malformed URLs
- Numerical features derived from missing components were set to be 0
- Categorical components were ignored in modelling

### Feature Encoding
- Converted categorical signals into numerical indicators:
  - `has_https`
  - `url_has_ipv4`
  - `url_has_port`
- Boolean features converted to integers

### Feature Consolidation
- Combined all the numerical features into a single dataset:
  - 30 features (ignored Hexadecimal features)
  - 2,53,051 rows
- Target variable:
  - `class = 1` (phishing)
  - `class = 0` (legitimate)

### Removing duplicates
- Removed 33,312 duplicate rows
- Final processed dataset is saved as:
```
data/processed/processed_data.csv
```

## 4. Model Training & Evaluation

### Models Trained
- **Random Forest Classifier**
- **XGBoost Classifier**

### Performance Comparision
| Model         | Test Accuracy | Precision   | Recall      |
| :-------------: | :-------------: | :-----------: | :-----------: |
| Random Forest | ~97.75%       | ~98.67%     | ~96.69%     |
| XGBoost       | **~98.28%**   | **~99.36%** | **~97.05%** |

**XGBoost outperformed Random Forest, especially in generalization.**

### Feature Importance (SHAP Analysis)
Top influential features:
- HTTPS presence
- Dot count in Domain
- Domain Entropy
- SLD Length
- Path Length
- URL Depth
- Digit count
- Path entropy

Low-impact features removed:
- total_tokens
- sld_token_count
- url_has_ipv4
- url_has_port

### Hyperparameter Tuning
Hyperparameter tuning was performed to optimize the model's performance and improve generalization using `hyperopt`. Key hyperparameters were adjusted using cross-validation. After hyperparameter tuning, the model's recall is slightly increased while the remaining metrics are unchanged.

### Threshold Optimization
By adding a minimum recall constraint (≥ 0.9725) and a threshold constraint (≥ 0.45), the selected operating point improves recall to 0.9725 while preserving high precision (0.9904). Overall performance remains stable, with an F1-score of 0.9821 and 98% accuracy, indicating no meaningful trade-off in model quality.