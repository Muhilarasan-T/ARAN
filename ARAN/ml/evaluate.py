"""
ARAN — Model Evaluation
=========================

What are we doing?
------------------
We evaluate the trained XGBoost model using multiple metrics beyond accuracy.

Why not just use accuracy?
---------------------------
Accuracy is misleading for imbalanced classes.
Example: if 95% of sessions are human, a model that always predicts "human"
gets 95% accuracy but detects exactly 0 bots.

For bot detection, we care about:
  - Precision: When we call it a bot, are we right? (minimize false positives)
  - Recall: Of all real bots, how many did we catch? (minimize false negatives)
  - F1: Harmonic mean of precision and recall
  - ROC-AUC: Overall discrimination ability across all thresholds

Interview concept: Precision vs Recall trade-off
--------------------------------------------------
False Positive (FP): We flag a legitimate user as a bot → user gets blocked → bad UX
False Negative (FN): We miss a bot → bot continues attacking → security risk

For bot detection, we want HIGH recall (catch most bots) while keeping
precision acceptable (don't block too many real users).

The threshold (default 0.5) can be tuned: lowering it increases recall
but decreases precision. Raising it increases precision but misses more bots.

Run:
----
  cd ARAN/ml
  python evaluate.py
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    f1_score,
)
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "traffic_dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "xgboost_model.pkl")
PREPROCESSOR_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "preprocessor.pkl")
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "plots")
SEED = 42


def load_test_set():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.20, random_state=SEED, stratify=y)
    return X_test, y_test


def evaluate():
    os.makedirs(PLOTS_DIR, exist_ok=True)

    print("Loading model and test data…")
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    X_test, y_test = load_test_set()
    X_test_scaled = preprocessor.transform(X_test)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    # ==================================================================
    # 1. Classification Report
    # ==================================================================
    print("\n" + "=" * 60)
    print("Classification Report")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=["Human (0)", "Bot (1)"]))

    # ==================================================================
    # 2. ROC-AUC
    # ==================================================================
    auc = roc_auc_score(y_test, y_proba)
    print(f"ROC-AUC Score: {auc:.4f}")

    # ==================================================================
    # 3. Confusion Matrix
    # ==================================================================
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives  (correctly identified humans): {tn}")
    print(f"  False Positives (humans flagged as bots):      {fp}  ← Bad UX")
    print(f"  False Negatives (bots we missed):              {fn}  ← Security risk")
    print(f"  True Positives  (correctly detected bots):     {tp}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("ARAN — XGBoost Model Evaluation", fontsize=14, fontweight="bold")

    # Confusion matrix heatmap
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["Human", "Bot"], yticklabels=["Human", "Bot"],
        ax=axes[0]
    )
    axes[0].set_title("Confusion Matrix")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    axes[1].plot(fpr, tpr, color="#4F9CF9", lw=2, label=f"XGBoost (AUC = {auc:.3f})")
    axes[1].plot([0, 1], [0, 1], "k--", lw=1, label="Random classifier")
    axes[1].set_xlabel("False Positive Rate")
    axes[1].set_ylabel("True Positive Rate")
    axes[1].set_title("ROC Curve")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(PLOTS_DIR, "evaluation.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"\n✅ Evaluation plots saved to: {plot_path}")
    plt.show()

    # ==================================================================
    # 4. Threshold Analysis
    # ==================================================================
    print("\nThreshold Sensitivity:")
    print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    for thresh in [0.3, 0.4, 0.5, 0.6, 0.7]:
        y_thresh = (y_proba >= thresh).astype(int)
        p = (y_thresh[y_test == 1] == 1).mean() if y_thresh.sum() > 0 else 0
        r = (y_thresh[y_test == 1] == 1).mean()
        f = f1_score(y_test, y_thresh, zero_division=0)
        print(f"{thresh:>10.1f} {p:>10.3f} {r:>10.3f} {f:>10.3f}")

    return auc


if __name__ == "__main__":
    evaluate()
