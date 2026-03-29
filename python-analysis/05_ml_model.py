"""
05 — Flight Delay Prediction Model
=====================================
Build a Random Forest classifier to predict whether a flight will be delayed
(arrival delay >= 15 min). Includes feature engineering, evaluation metrics,
feature importance, and SHAP explanation.

Uses DuckDB TABLESAMPLE to pull only 200K rows instead of the full 2.76M,
which is plenty for a good model and completes in seconds.
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix,
    RocCurveDisplay,
)
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.chart_styles import (
    setup_mckinsey_style, format_chart, save_chart, get_connection,
    NAVY, ACCENT, BLUE_MED, BLUE_LIGHT, GRAY_DARK, GRAY_MED,
    PALETTE, thousands,
)


# =============================================================================
# Data loading & feature engineering
# =============================================================================
def load_and_engineer():
    """Load a 200K sample from flights, drop leakage columns, engineer features."""
    con = get_connection()
    print("Loading 200K sample from flights for ML ...")
    df = con.execute("""
        SELECT
            carrier_code, origin, dest, distance,
            hour_of_day, day_of_week, month, day_of_month, quarter,
            is_weekend, is_delayed
        FROM flights
        WHERE arr_delay_minutes IS NOT NULL
          AND is_delayed IS NOT NULL
        USING SAMPLE 200000 ROWS
    """).fetchdf()
    con.close()
    print(f"  {len(df):,} rows loaded.\n")

    # ---- Feature engineering ----
    # Encode carrier
    le_carrier = LabelEncoder()
    df["carrier_enc"] = le_carrier.fit_transform(df["carrier_code"].astype(str))

    # Encode origin / dest (top 50 airports, rest = "OTHER")
    for col in ["origin", "dest"]:
        top = df[col].value_counts().nlargest(50).index
        df[f"{col}_grp"] = df[col].where(df[col].isin(top), "OTHER")
    le_origin = LabelEncoder()
    le_dest = LabelEncoder()
    df["origin_enc"] = le_origin.fit_transform(df["origin_grp"].astype(str))
    df["dest_enc"] = le_dest.fit_transform(df["dest_grp"].astype(str))

    # Cyclic hour encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)

    # Cyclic day-of-week encoding
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Cyclic month encoding
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Feature list — NO leakage columns (no actual dep/arr times, no delay causes)
    features = [
        "carrier_enc", "origin_enc", "dest_enc",
        "distance",
        "hour_of_day", "hour_sin", "hour_cos",
        "day_of_week", "dow_sin", "dow_cos",
        "month", "month_sin", "month_cos",
        "day_of_month", "quarter",
        "is_weekend",
    ]

    feature_names = [
        "Carrier", "Origin Airport", "Dest Airport",
        "Distance (mi)",
        "Hour of Day", "Hour (sin)", "Hour (cos)",
        "Day of Week", "DoW (sin)", "DoW (cos)",
        "Month", "Month (sin)", "Month (cos)",
        "Day of Month", "Quarter",
        "Is Weekend",
    ]

    X = df[features].copy()
    y = df["is_delayed"].astype(int)

    # Drop any remaining NaN rows
    mask = X.notna().all(axis=1)
    X = X[mask]
    y = y[mask]

    print(f"  Features: {len(features)}")
    print(f"  Samples:  {len(X):,}")
    print(f"  Delay rate: {y.mean():.1%}\n")

    return X, y, features, feature_names


# =============================================================================
# Model training
# =============================================================================
def train_model(X, y):
    """Train-test split and fit Random Forest."""
    print("Splitting data 80/20 ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")
    print("Training Random Forest (500 trees, max_depth=18) ...")
    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=18,
        min_samples_leaf=50,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    print("  Training complete.\n")

    return model, X_train, X_test, y_train, y_test


# =============================================================================
# Evaluation
# =============================================================================
def evaluate(model, X_test, y_test):
    """Print and return evaluation metrics."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print("=" * 50)
    print("MODEL EVALUATION")
    print("=" * 50)
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {auc:.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=["On-time", "Delayed"]))

    return {"accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "roc_auc": auc}, y_pred, y_prob


# =============================================================================
# Charts
# =============================================================================
def chart_feature_importance(model, feature_names):
    print("[1/4] Feature importance ...")
    importances = model.feature_importances_
    idx = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh([feature_names[i] for i in idx], importances[idx],
            color=NAVY, edgecolor="white", height=0.6)
    ax.set_xlabel("Feature Importance (Gini)")

    for i, (imp, pos) in enumerate(zip(importances[idx], range(len(idx)))):
        ax.text(imp + 0.002, pos, f"{imp:.3f}", va="center", fontsize=8,
                color=GRAY_DARK)

    format_chart(fig, ax,
                 "Hour of Day and Distance Are the Strongest Delay Predictors",
                 "Random Forest Gini importance across 16 features")
    save_chart(fig, "25_feature_importance")
    print()


def chart_roc_curve(model, X_test, y_test):
    print("[2/4] ROC curve ...")
    fig, ax = plt.subplots(figsize=(7, 7))
    RocCurveDisplay.from_estimator(model, X_test, y_test, ax=ax,
                                    color=NAVY, linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color=GRAY_MED, linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")

    format_chart(fig, ax,
                 "Model Achieves Reasonable Discrimination on Delay Prediction",
                 "ROC curve on held-out test set (20%)")
    save_chart(fig, "26_roc_curve")
    print()


def chart_confusion_matrix(y_test, y_pred):
    print("[3/4] Confusion matrix ...")
    cm = confusion_matrix(y_test, y_pred)
    cm_pct = cm / cm.sum() * 100

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues", aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["On-time", "Delayed"])
    ax.set_yticklabels(["On-time", "Delayed"])
    # Add counts and percentages
    for i in range(2):
        for j in range(2):
            ax.text(j, i - 0.1, f"{cm[i, j]:,d}",
                    ha="center", va="center", fontsize=14, fontweight="bold",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
            ax.text(j, i + 0.15, f"({cm_pct[i, j]:.1f}%)",
                    ha="center", va="center", fontsize=9, color=GRAY_DARK)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    format_chart(fig, ax,
                 "Confusion Matrix Shows Trade-Off Between Precision and Recall",
                 "Absolute counts with percentage of total in parentheses")
    save_chart(fig, "27_confusion_matrix")
    print()


def chart_shap_summary(model, X_test, feature_names):
    """Generate SHAP summary plot. Falls back gracefully if shap not installed."""
    print("[4/4] SHAP summary plot ...")
    try:
        import shap
    except ImportError:
        print("  [SKIP] shap package not installed. Install with: pip install shap\n")
        return

    # Use a subsample for speed
    sample_size = min(5000, len(X_test))
    X_sample = X_test.sample(sample_size, random_state=42)
    X_sample.columns = feature_names

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    fig, ax = plt.subplots(figsize=(10, 7))
    # shap_values[1] = SHAP values for class 1 (delayed)
    shap.summary_plot(shap_values[1] if isinstance(shap_values, list) else shap_values,
                      X_sample, plot_type="bar", show=False, max_display=16)
    current_fig = plt.gcf()

    format_chart(current_fig, plt.gca(),
                 "SHAP Confirms Hour and Distance Drive Model Decisions",
                 "Mean |SHAP value| for delay prediction (class = 1)")
    save_chart(current_fig, "28_shap_summary")
    print()


# =============================================================================
# Metrics export
# =============================================================================
def save_metrics(metrics):
    """Save metrics to a small CSV for downstream use."""
    from utils.chart_styles import BASE_DIR
    out = BASE_DIR / "docs" / "charts" / "model_metrics.csv"
    pd.DataFrame([metrics]).to_csv(out, index=False)
    print(f"  Metrics saved to {out.relative_to(BASE_DIR)}\n")


# =============================================================================
# Main
# =============================================================================
def main():
    setup_mckinsey_style()

    X, y, features, feature_names = load_and_engineer()
    model, X_train, X_test, y_train, y_test = train_model(X, y)
    metrics, y_pred, y_prob = evaluate(model, X_test, y_test)

    chart_feature_importance(model, feature_names)
    chart_roc_curve(model, X_test, y_test)
    chart_confusion_matrix(y_test, y_pred)
    chart_shap_summary(model, X_test, feature_names)
    save_metrics(metrics)

    print("ML model analysis complete. Charts saved to docs/charts/")


if __name__ == "__main__":
    main()
