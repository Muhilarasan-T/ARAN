# ARAN — Real-Time API Bot Detection & Automated Mitigation

> **Intelligent Protection Against Automated API Abuse**

ARAN is a portfolio-grade, full-stack Machine Learning project demonstrating real-time API bot detection using XGBoost, behavioral feature engineering, SHAP explainability, FastAPI, React, and WebSockets.

---

## Quick Start

The easiest way to run the entire stack is with Docker:

```bash
cd ARAN
docker-compose up --build
```
> Then open `http://localhost:5173` in your browser.

---

### Manual Setup (Without Docker)

#### 1. Install Python dependencies

```bash
cd ARAN/backend
pip install -r requirements.txt
```

### 2. Generate the dataset & train the model

```bash
cd ARAN/ml
pip install -r requirements.txt
python data_generator.py   # → data/raw/traffic_dataset.csv
python train.py            # → models/xgboost_model.pkl + models/preprocessor.pkl
python evaluate.py         # Optional: view metrics & plots
python explain.py          # Optional: SHAP feature importance
```

### 3. Start the FastAPI backend

```bash
cd ARAN/backend
uvicorn main:app --reload --port 8000
```

### 4. Start the React frontend

> **Node.js required.** Install from https://nodejs.org

```bash
cd ARAN/frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Project Structure

```
ARAN/
├── frontend/          React + Vite UI (5 pages, WebSocket, premium dark theme)
├── backend/
│   ├── main.py        FastAPI application entry point
│   ├── routes/        demo_api, protection, mitigation
│   ├── services/      inference, feature_extractor, explainer, mitigation_engine
│   ├── websocket/     WebSocket manager (real-time events)
│   ├── simulation/    normal_user.py, bot_attack.py
│   └── config.py      Risk thresholds, paths, settings
├── ml/
│   ├── data_generator.py   Synthetic dataset (5,000 sessions)
│   ├── feature_engineering.py  13-feature schema with explanations
│   ├── train.py         Baseline + RF + XGBoost + GridSearchCV
│   ├── evaluate.py      Precision/Recall/F1/AUC/Confusion matrix
│   └── explain.py       SHAP global + local explanation
├── data/raw/          traffic_dataset.csv (generated)
└── models/            xgboost_model.pkl + preprocessor.pkl (generated)
```

---

## ML Pipeline

| Step | What | Why |
|---|---|---|
| Synthetic data | 3,000 human + 2,000 bot sessions | Realistic behavioral differences |
| 13 features | request rate, entropy, variance, failure ratio, etc. | Quantify bot vs human behavior |
| Standard Scaler | Fit on train only | Prevent data leakage |
| Logistic Regression | Baseline | Quantify XGBoost uplift |
| Random Forest | Comparison | Non-linear benchmark |
| **XGBoost** | **Production model** | Best accuracy on tabular data |
| GridSearchCV | Hyperparameter tuning | Generalization without overfitting |
| SHAP | Per-prediction explanation | Transparency and trust |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router, WebSocket |
| Backend | Python, FastAPI, Uvicorn |
| ML | Pandas, NumPy, Scikit-learn, XGBoost, SHAP |
| Real-time | WebSocket (FastAPI native) |

---

## User Flow

```
Landing → Try Demo → Shopping API → Start Protection
→ [Normal User | Bot Attack]
→ Real HTTP requests → Feature extraction → XGBoost inference
→ Bot probability → Risk level → SHAP explanation
→ Mitigation (Allow / Rate Limit / Block)
→ Result displayed in real time via WebSocket
```

---

## ML Concepts Demonstrated

- Synthetic dataset generation with realistic noise
- EDA and class distribution analysis
- 13 behavioral features (entropy, variance, failure ratios)
- Train/test split without data leakage
- Baseline model comparison (LR → RF → XGBoost)
- Gradient boosting with hyperparameter tuning
- Precision vs Recall trade-off in security context
- ROC-AUC and confusion matrix analysis
- SHAP feature attribution (global + local)
- Model serialization with joblib
- Real-time inference without model retraining

---

## Configuration

Copy `.env.example` to `.env` to override defaults:

```
RISK_LOW_MAX=0.40
RISK_MEDIUM_MAX=0.75
BLOCK_DURATION_SECONDS=600
```

---

*Built as a Data Science portfolio project demonstrating end-to-end ML engineering.*
