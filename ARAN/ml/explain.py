"""
ARAN — Model Explainability
=============================

What are we doing?
------------------
We use SHAP (SHapley Additive exPlanations) to explain:
  1. GLOBAL: Which features are most important overall?
  2. LOCAL: For a specific prediction, which features drove the decision?

Why SHAP?
----------
SHAP provides theoretically grounded explanations based on game theory
(Shapley values). Unlike feature importance from XGBoost (which is based
on how often a feature was used in splits), SHAP shows the DIRECTION
of each feature's contribution — positive SHAP means pushed toward bot.

Interview concept: SHAP
-------------------------
SHAP values answer: "How much did feature X contribute to this prediction?"
For a prediction of bot_probability = 0.94:
  request_interval_variance → SHAP = -1.8  (very low variance pushed strongly toward bot)
  requests_per_minute → SHAP = +1.2        (high rate pushed toward bot)
  endpoint_entropy → SHAP = -0.9           (low entropy pushed toward bot)

Note on sign convention: SHAP can be confusing because the sign depends on
the direction of classification. We use shap_values for class 1 (bot).
Positive SHAP = feature pushed toward "bot". Negative SHAP = pushed toward "human".

Run:
----
  cd ARAN/ml
  python explain.py
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import shap

from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "traffic_dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "xgboost_model.pkl")
PREPROCESSOR_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "preprocessor.pkl")
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "plots")
SEED = 42


def run_shap_analysis():
    os.makedirs(PLOTS_DIR, exist_ok=True)

    print("Loading model, preprocessor, and data…")
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.20, random_state=SEED, stratify=y)

    X_test_scaled = preprocessor.transform(X_test)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=FEATURE_COLUMNS)

    # ==================================================================
    # SHAP TreeExplainer — fast, exact for tree-based models
    # ==================================================================
    print("Computing SHAP values…")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_scaled_df)

    # For binary classification, shap_values may be a list [class0, class1]
    if isinstance(shap_values, list):
        shap_vals_bot = shap_values[1]
    else:
        shap_vals_bot = shap_values

    # ==================================================================
    # 1. Global Feature Importance (mean absolute SHAP)
    # ==================================================================
    mean_abs_shap = np.abs(shap_vals_bot).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "mean_abs_shap": mean_abs_shap
    }).sort_values("mean_abs_shap", ascending=True)

    print("\nGlobal Feature Importance (SHAP):")
    for _, row in importance_df.iterrows():
        bar = "█" * int(row["mean_abs_shap"] * 10)
        print(f"  {row['feature']:35s} {bar} {row['mean_abs_shap']:.4f}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("ARAN — SHAP Model Explainability", fontsize=14, fontweight="bold")

    # Bar chart
    axes[0].barh(
        importance_df["feature"],
        importance_df["mean_abs_shap"],
        color="#4F9CF9"
    )
    axes[0].set_title("Global Feature Importance (mean |SHAP value|)")
    axes[0].set_xlabel("Mean |SHAP|")
    axes[0].grid(axis="x", alpha=0.3)

    # ==================================================================
    # 2. Sample local explanation for a detected bot
    # ==================================================================
    bot_indices = np.where(y_test.values == 1)[0]
    sample_idx = bot_indices[0]

    local_shap = shap_vals_bot[sample_idx]
    local_features = X_test_scaled_df.iloc[sample_idx]
    local_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "shap_value": local_shap,
        "feature_value": local_features.values
    }).sort_values("shap_value", ascending=True)

    colors = ["#ef4444" if v > 0 else "#22c55e" for v in local_df["shap_value"]]
    axes[1].barh(local_df["feature"], local_df["shap_value"], color=colors)
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].set_title("Local Explanation — Single Bot Prediction\n(Red = pushes toward Bot, Green = pushes toward Human)")
    axes[1].set_xlabel("SHAP Value")
    axes[1].grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(PLOTS_DIR, "shap_explanation.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"\n✅ SHAP plots saved to: {plot_path}")
    plt.show()


if __name__ == "__main__":
    run_shap_analysis()
