"""
ARAN — Model Training Pipeline
================================

What are we doing?
------------------
We train a binary classifier to predict whether an API session is from a bot.
We follow this sequence:
  1. Load the dataset
  2. Split into train and test sets (to evaluate generalization)
  3. Preprocess features (scaling)
  4. Train a Logistic Regression baseline
  5. Train a Random Forest for comparison
  6. Train the final XGBoost model
  7. Save the XGBoost model and preprocessor to disk

Interview concept: Why XGBoost?
--------------------------------
XGBoost is a gradient boosting framework. It builds an ensemble of decision trees
where each new tree corrects the errors of the previous one. Advantages:
  - Handles non-linear feature interactions naturally (unlike Logistic Regression)
  - Built-in regularization to prevent overfitting
  - Fast training with native parallelism
  - Returns predict_proba() — we get a probability, not just 0/1
  - Feature importance built-in — explainability by default
  - Industry standard for tabular classification tasks

Interview concept: train_test_split
-------------------------------------
We split data BEFORE any preprocessing (fitting StandardScaler, etc.).
Why? If we scale the full dataset and THEN split, the test set statistics
"leaked" into training — the model has cheated by seeing the test data
during normalization. Always: split first, fit preprocessor on train,
transform both train and test.

Run:
----
  cd ARAN/ml
  python train.py
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

# Ensure consistent imports whether run from ml/ or root
sys.path.insert(0, os.path.dirname(__file__))
from feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN

# Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "traffic_dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "xgboost_model.pkl")
PREPROCESSOR_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "preprocessor.pkl")

SEED = 42
TEST_SIZE = 0.20  # 80% train, 20% test


# ===========================================================================
# 1. Load Data
# ===========================================================================
def load_data() -> tuple:
    """
    Load dataset and split into feature matrix X and labels y.

    Interview: Why not just use all columns?
    ----------------------------------------
    We explicitly select FEATURE_COLUMNS to ensure the exact same features
    are used in both training and inference. If we accidentally included
    a column like 'session_id' or 'is_bot' in X, the model would either
    cheat (data leakage) or crash during inference.
    """
    print(f"Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    print(f"Shape: {df.shape}")
    print(f"Class distribution:\n{df[TARGET_COLUMN].value_counts()}")
    print(f"Missing values: {df.isnull().sum().sum()}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    return X, y


# ===========================================================================
# 2. Split — BEFORE preprocessing to prevent data leakage
# ===========================================================================
def split_data(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Split data into train and test sets.

    Interview concept: Why 80/20?
    ------------------------------
    With 5,000 samples, 20% = 1,000 test samples — enough for stable metrics.
    For very small datasets, k-fold cross-validation is better.
    stratify=y ensures both splits have the same bot/human ratio.
    random_state ensures reproducibility.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y
    )
    print(f"\nTrain size: {X_train.shape[0]} | Test size: {X_test.shape[0]}")
    print(f"Train bot rate: {y_train.mean():.2%} | Test bot rate: {y_test.mean():.2%}")
    return X_train, X_test, y_train, y_test


# ===========================================================================
# 3. Preprocessing — fit on train ONLY
# ===========================================================================
def build_preprocessor(X_train: pd.DataFrame) -> StandardScaler:
    """
    Fit a StandardScaler on training data.

    Interview concept: StandardScaler
    -----------------------------------
    StandardScaler transforms each feature to have mean=0 and std=1.
    Formula: z = (x - mean) / std
    This prevents features with large ranges (e.g. requests_per_minute: 0–800)
    from dominating features with small ranges (e.g. failed_ratio: 0–1).
    XGBoost doesn't strictly require scaling, but it doesn't hurt and ensures
    consistent behavior when we switch models.

    CRITICAL: We fit ONLY on X_train. If we fit on X_train + X_test,
    we leak test statistics into training — the model has seen the test
    distribution, which inflates eval metrics.
    """
    scaler = StandardScaler()
    scaler.fit(X_train)
    return scaler


# ===========================================================================
# 4. Baseline — Logistic Regression
# ===========================================================================
def train_baseline(X_train, X_test, y_train, y_test, preprocessor) -> dict:
    """
    Train a Logistic Regression baseline.

    Interview concept: Why start with a baseline?
    -----------------------------------------------
    A baseline tells you the minimum acceptable performance.
    If XGBoost barely beats Logistic Regression, the dataset might not have
    enough non-linear signal, or you have data quality issues.
    If it crushes Logistic Regression, XGBoost is genuinely adding value.
    """
    print("\n--- Baseline: Logistic Regression ---")
    X_train_scaled = preprocessor.transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    lr = LogisticRegression(max_iter=500, random_state=SEED)
    lr.fit(X_train_scaled, y_train)

    preds = lr.predict(X_test_scaled)
    proba = lr.predict_proba(X_test_scaled)[:, 1]
    auc = roc_auc_score(y_test, proba)

    print(classification_report(y_test, preds, target_names=["Human", "Bot"]))
    print(f"ROC-AUC: {auc:.4f}")
    return {"model": lr, "auc": auc}


# ===========================================================================
# 5. Random Forest comparison
# ===========================================================================
def train_random_forest(X_train, X_test, y_train, y_test, preprocessor) -> dict:
    """
    Train a Random Forest for comparison.

    Interview concept: Ensemble methods
    -------------------------------------
    Random Forest trains multiple decision trees, each on a random subset
    of features and data. Final prediction is majority vote (or average proba).
    It handles non-linearity better than Logistic Regression but is usually
    slower and less accurate than XGBoost on tabular data.
    """
    print("\n--- Comparison: Random Forest ---")
    X_train_scaled = preprocessor.transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    rf = RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)

    preds = rf.predict(X_test_scaled)
    proba = rf.predict_proba(X_test_scaled)[:, 1]
    auc = roc_auc_score(y_test, proba)

    print(classification_report(y_test, preds, target_names=["Human", "Bot"]))
    print(f"ROC-AUC: {auc:.4f}")
    return {"model": rf, "auc": auc}


# ===========================================================================
# 6. XGBoost — Final production model
# ===========================================================================
def train_xgboost(X_train, X_test, y_train, y_test, preprocessor) -> dict:
    """
    Train and tune the XGBoost classifier.

    Interview concept: XGBoost hyperparameters
    -------------------------------------------
    n_estimators: Number of trees. More = slower, potentially better (but overfits eventually).
    max_depth: Depth of each tree. Deeper = more complex patterns but overfits. 3–6 is typical.
    learning_rate: How much each tree contributes. Lower + more trees = better generalization.
    subsample: Fraction of training samples per tree. < 1.0 = stochastic, reduces overfitting.
    colsample_bytree: Fraction of features per tree. Regularization + diversity.
    scale_pos_weight: Handles class imbalance. ratio = n_negative / n_positive.

    Interview concept: Overfitting
    --------------------------------
    Overfitting = model memorizes training data but fails on new data.
    Signs: training accuracy >> test accuracy.
    Solutions: regularization (lambda, alpha), reduce max_depth, reduce n_estimators,
    use subsample/colsample, early stopping.
    """
    print("\n--- Final Model: XGBoost ---")
    X_train_scaled = preprocessor.transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)

    # Class imbalance handling
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    print(f"scale_pos_weight: {scale_pos_weight:.2f}")

    # Hyperparameter grid (kept small for demo — not excessive)
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [3, 5],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8],
        "colsample_bytree": [0.8],
    }

    base_xgb = XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        random_state=SEED,
        eval_metric="logloss",
        use_label_encoder=False,
        verbosity=0,
    )

    print("Running GridSearchCV (3-fold CV)…")
    grid_search = GridSearchCV(
        base_xgb, param_grid, cv=3, scoring="roc_auc",
        n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train_scaled, y_train)

    best_xgb = grid_search.best_estimator_
    print(f"Best params: {grid_search.best_params_}")
    print(f"Best CV AUC: {grid_search.best_score_:.4f}")

    preds = best_xgb.predict(X_test_scaled)
    proba = best_xgb.predict_proba(X_test_scaled)[:, 1]
    auc = roc_auc_score(y_test, proba)

    print("\nTest set results:")
    print(classification_report(y_test, preds, target_names=["Human", "Bot"]))
    print(f"Test ROC-AUC: {auc:.4f}")

    return {
        "model": best_xgb,
        "auc": auc,
        "best_params": grid_search.best_params_,
        "y_pred": preds,
        "y_proba": proba,
    }


# ===========================================================================
# 7. Save model artifacts
# ===========================================================================
def save_artifacts(model, preprocessor):
    """
    Persist the trained model and preprocessor using joblib.

    Interview concept: Model serialization
    ----------------------------------------
    joblib.dump() serializes a Python object to disk using pickle + compression.
    The saved file contains the entire fitted model (weights, hyperparameters, etc.).
    joblib.load() restores it — the loaded model behaves identically to the original.

    Alternative: ONNX format for language-agnostic serving.
    For this project, joblib is sufficient since both training and serving use Python.

    CRITICAL: Save BOTH the model AND the preprocessor.
    At inference time, raw features must be scaled using the SAME scaler
    that was fitted on training data. If you re-fit the scaler on new data,
    the transformation will differ → wrong predictions.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"\n✅ Model saved to:       {MODEL_PATH}")
    print(f"✅ Preprocessor saved to: {PREPROCESSOR_PATH}")


# ===========================================================================
# Main
# ===========================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("ARAN — ML Training Pipeline")
    print("=" * 60)

    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    preprocessor = build_preprocessor(X_train)

    # Train all models
    lr_result = train_baseline(X_train, X_test, y_train, y_test, preprocessor)
    rf_result = train_random_forest(X_train, X_test, y_train, y_test, preprocessor)
    xgb_result = train_xgboost(X_train, X_test, y_train, y_test, preprocessor)

    # Summary
    print("\n" + "=" * 60)
    print("Model Comparison:")
    print(f"  Logistic Regression AUC: {lr_result['auc']:.4f}")
    print(f"  Random Forest AUC:       {rf_result['auc']:.4f}")
    print(f"  XGBoost AUC:             {xgb_result['auc']:.4f}")
    print("=" * 60)

    # Save the best model (XGBoost)
    save_artifacts(xgb_result["model"], preprocessor)

    print("\n🎉 Training complete! The model is ready for the ARAN API.")
