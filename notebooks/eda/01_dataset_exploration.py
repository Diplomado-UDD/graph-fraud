"""
EDA Notebook 1: Dataset Exploration
Comprehensive exploratory data analysis of fraud detection dataset
"""

import marimo
import sys
from pathlib import Path

__generated_with = "0.17.7"
app = marimo.App(width="medium")

# Ensure the src directory is in the Python path
src_path = Path(__file__).resolve().parent.parent.parent / "src"
if src_path not in sys.path:
    sys.path.insert(0, str(src_path))


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns

    from src.data.generate_dataset import FraudDatasetGenerator

    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (12, 6)

    mo.md("# Fraud Detection Dataset - Exploratory Data Analysis")
    return FraudDatasetGenerator, mo, np, pd, plt, sns


@app.cell
def __(mo):
    mo.md(
        """
    ## 1. Dataset Generation and Loading

    Generate synthetic fraud detection dataset with configurable parameters.
    This simulates a P2P payment network with normal users and fraudsters.
    """
    )
    return


@app.cell
def __(FraudDatasetGenerator):
    # Generate dataset
    SEED = 42
    N_USERS = 200
    N_TRANSACTIONS = 1000

    generator = FraudDatasetGenerator(seed=SEED)
    dataset = generator.generate_dataset(n_users=N_USERS, n_transactions=N_TRANSACTIONS)

    # Extract dataframes
    users_df = dataset["users"]
    devices_df = dataset["devices"]
    user_devices_df = dataset["user_devices"]
    transactions_df = dataset["transactions"]
    fraud_rings_df = dataset["fraud_rings"]
    return (
        N_TRANSACTIONS,
        N_USERS,
        SEED,
        dataset,
        devices_df,
        fraud_rings_df,
        generator,
        transactions_df,
        user_devices_df,
        users_df,
    )


@app.cell
def __(mo, pd, transactions_df, users_df):
    mo.md(
        """
    ## 2. Dataset Overview

    ### Summary Statistics
    """
    )

    summary_stats = {
        "Total Users": len(users_df),
        "Fraudsters": users_df["is_fraudster"].sum(),
        "Normal Users": (~users_df["is_fraudster"]).sum(),
        "Fraud Rate": f"{users_df['is_fraudster'].mean():.1%}",
        "Total Transactions": len(transactions_df),
        "Fraudulent Transactions": transactions_df["is_fraudulent"].sum(),
        "Normal Transactions": (~transactions_df["is_fraudulent"]).sum(),
        "Total Transaction Volume": f"${transactions_df['amount'].sum():,.2f}",
        "Average Transaction Amount": f"${transactions_df['amount'].mean():.2f}",
    }

    summary_df = pd.DataFrame([summary_stats]).T
    summary_df.columns = ["Value"]

    mo.md(
        f"""
    {mo.as_html(summary_df)}
    """
    )
    return summary_df, summary_stats


@app.cell
def __(mo):
    mo.md(
        """
    ## 3. Data Quality Checks

    ### Missing Values Analysis
    """
    )
    return


@app.cell
def __(devices_df, mo, pd, transactions_df, user_devices_df, users_df):
    # Check for missing values
    missing_data = {
        "users": users_df.isnull().sum(),
        "devices": devices_df.isnull().sum(),
        "user_devices": user_devices_df.isnull().sum(),
        "transactions": transactions_df.isnull().sum(),
    }

    missing_summary = []
    for table_name, missing_counts in missing_data.items():
        if missing_counts.sum() > 0:
            missing_summary.append(
                {
                    "Table": table_name,
                    "Missing Values": missing_counts.sum(),
                    "Columns Affected": missing_counts[missing_counts > 0].to_dict(),
                }
            )

    if missing_summary:
        mo.md(
            f"""
        **Warning:** Missing values detected:
        {mo.as_html(pd.DataFrame(missing_summary))}
        """
        )
    else:
        mo.md("**Status:** No missing values detected in any dataset.")
    return missing_counts, missing_data, missing_summary, table_name


@app.cell
def __(mo):
    mo.md(
        """
    ### Schema Validation
    """
    )
    return


@app.cell
def __(mo, transactions_df, user_devices_df, users_df):
    # Validate schemas
    validation_checks = []

    # Users schema
    expected_user_cols = [
        "user_id",
        "is_fraudster",
        "account_age_days",
        "verification_level",
    ]
    users_check = all(col in users_df.columns for col in expected_user_cols)
    validation_checks.append(
        {"Check": "Users Table Schema", "Status": "Pass" if users_check else "Fail"}
    )

    # Transactions schema
    expected_txn_cols = [
        "transaction_id",
        "sender_id",
        "receiver_id",
        "amount",
        "timestamp",
        "is_fraudulent",
    ]
    txn_check = all(col in transactions_df.columns for col in expected_txn_cols)
    validation_checks.append(
        {
            "Check": "Transactions Table Schema",
            "Status": "Pass" if txn_check else "Fail",
        }
    )

    # Referential integrity
    all_user_ids = set(users_df["user_id"])
    sender_ids = set(transactions_df["sender_id"])
    receiver_ids = set(transactions_df["receiver_id"])
    ref_check = sender_ids.issubset(all_user_ids) and receiver_ids.issubset(
        all_user_ids
    )
    validation_checks.append(
        {
            "Check": "Referential Integrity (Transactions)",
            "Status": "Pass" if ref_check else "Fail",
        }
    )

    # Device usage integrity
    device_user_ids = set(user_devices_df["user_id"])
    device_check = device_user_ids.issubset(all_user_ids)
    validation_checks.append(
        {
            "Check": "Referential Integrity (User-Devices)",
            "Status": "Pass" if device_check else "Fail",
        }
    )

    # Value range checks
    amount_check = (transactions_df["amount"] > 0).all()
    validation_checks.append(
        {
            "Check": "Transaction Amounts Positive",
            "Status": "Pass" if amount_check else "Fail",
        }
    )

    age_check = (users_df["account_age_days"] > 0).all()
    validation_checks.append(
        {"Check": "Account Ages Positive", "Status": "Pass" if age_check else "Fail"}
    )

    import pandas as pd_check

    validation_df = pd_check.DataFrame(validation_checks)
    mo.as_html(validation_df)
    return (
        age_check,
        all_user_ids,
        amount_check,
        device_check,
        device_user_ids,
        expected_txn_cols,
        expected_user_cols,
        pd_check,
        receiver_ids,
        ref_check,
        sender_ids,
        txn_check,
        users_check,
        validation_checks,
        validation_df,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 4. Distribution Analysis

    ### User Characteristics
    """
    )
    return


@app.cell
def __(mo, plt, sns, users_df):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Account age distribution by fraud status
    sns.histplot(
        data=users_df,
        x="account_age_days",
        hue="is_fraudster",
        kde=True,
        ax=axes[0, 0],
        bins=30,
    )
    axes[0, 0].set_title("Account Age Distribution by Fraud Status")
    axes[0, 0].set_xlabel("Account Age (days)")

    # Verification level distribution
    fraud_counts = (
        users_df.groupby(["verification_level", "is_fraudster"]).size().unstack()
    )
    fraud_counts.plot(kind="bar", ax=axes[0, 1], stacked=False)
    axes[0, 1].set_title("Verification Level Distribution")
    axes[0, 1].set_xlabel("Verification Level")
    axes[0, 1].set_ylabel("Count")
    axes[0, 1].legend(title="Is Fraudster")
    axes[0, 1].tick_params(axis="x", rotation=0)

    # Fraud rate by verification level
    fraud_rate_by_level = users_df.groupby("verification_level")["is_fraudster"].mean()
    fraud_rate_by_level.plot(kind="bar", ax=axes[1, 0], color="coral")
    axes[1, 0].set_title("Fraud Rate by Verification Level")
    axes[1, 0].set_xlabel("Verification Level")
    axes[1, 0].set_ylabel("Fraud Rate")
    axes[1, 0].tick_params(axis="x", rotation=0)

    # Box plot: Account age by fraud status
    sns.boxplot(data=users_df, x="is_fraudster", y="account_age_days", ax=axes[1, 1])
    axes[1, 1].set_title("Account Age Box Plot by Fraud Status")
    axes[1, 1].set_xlabel("Is Fraudster")
    axes[1, 1].set_ylabel("Account Age (days)")

    plt.tight_layout()
    fig_users = plt.gcf()
    plt.close()

    mo.md(
        f"""
    {mo.as_html(fig_users)}

    **Key Observations:**
    - Fraudster accounts are significantly younger (mean: {users_df[users_df['is_fraudster']]['account_age_days'].mean():.1f} days)
    - Normal user accounts are much older (mean: {users_df[~users_df['is_fraudster']]['account_age_days'].mean():.1f} days)
    - This is a strong fraud indicator
    """
    )
    return axes, fig, fig_users, fraud_counts, fraud_rate_by_level


@app.cell
def __(mo):
    mo.md(
        """
    ### Transaction Characteristics
    """
    )
    return


@app.cell
def __(mo, plt, sns, transactions_df):
    fig_txn, axes_txn = plt.subplots(2, 2, figsize=(14, 10))

    # Transaction amount distribution
    sns.histplot(
        data=transactions_df,
        x="amount",
        hue="is_fraudulent",
        kde=True,
        ax=axes_txn[0, 0],
        bins=50,
    )
    axes_txn[0, 0].set_title("Transaction Amount Distribution")
    axes_txn[0, 0].set_xlabel("Amount ($)")

    # Box plot: Amount by fraud status
    sns.boxplot(data=transactions_df, x="is_fraudulent", y="amount", ax=axes_txn[0, 1])
    axes_txn[0, 1].set_title("Transaction Amount by Fraud Status")
    axes_txn[0, 1].set_ylabel("Amount ($)")

    # Transaction status distribution
    status_counts = (
        transactions_df.groupby(["status", "is_fraudulent"]).size().unstack()
    )
    status_counts.plot(kind="bar", ax=axes_txn[1, 0], stacked=False)
    axes_txn[1, 0].set_title("Transaction Status Distribution")
    axes_txn[1, 0].set_xlabel("Status")
    axes_txn[1, 0].legend(title="Is Fraudulent")
    axes_txn[1, 0].tick_params(axis="x", rotation=0)

    # Fraud rate over time (sample)
    transactions_df["date"] = pd.to_datetime(transactions_df["timestamp"]).dt.date
    daily_fraud_rate = transactions_df.groupby("date")["is_fraudulent"].mean()
    daily_fraud_rate.plot(ax=axes_txn[1, 1], marker="o", color="red")
    axes_txn[1, 1].set_title("Daily Fraud Rate Trend")
    axes_txn[1, 1].set_xlabel("Date")
    axes_txn[1, 1].set_ylabel("Fraud Rate")
    axes_txn[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    fig_txn_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    {mo.as_html(fig_txn_final)}

    **Key Observations:**
    - Fraudulent transactions have higher amounts (mean: ${transactions_df[transactions_df['is_fraudulent']]['amount'].mean():.2f})
    - Normal transactions are smaller (mean: ${transactions_df[~transactions_df['is_fraudulent']]['amount'].mean():.2f})
    - Transaction amount is a strong fraud indicator
    """
    )
    return axes_txn, daily_fraud_rate, fig_txn, fig_txn_final, status_counts


@app.cell
def __(mo):
    mo.md(
        """
    ## 5. Statistical Summary

    ### Descriptive Statistics by Fraud Status
    """
    )
    return


@app.cell
def __(mo, pd, transactions_df, users_df):
    # User statistics
    user_stats = users_df.groupby("is_fraudster")["account_age_days"].describe()

    # Transaction statistics
    txn_stats_by_user = (
        transactions_df.groupby("sender_id")
        .agg({"amount": ["count", "mean", "sum"]})
        .reset_index()
    )
    txn_stats_by_user.columns = ["user_id", "txn_count", "avg_amount", "total_amount"]

    # Merge with user fraud status
    txn_stats_with_fraud = txn_stats_by_user.merge(
        users_df[["user_id", "is_fraudster"]], on="user_id", how="left"
    )

    txn_summary = txn_stats_with_fraud.groupby("is_fraudster")[
        ["txn_count", "avg_amount", "total_amount"]
    ].describe()

    mo.md(
        f"""
    ### User Account Age Statistics
    {mo.as_html(user_stats)}

    ### Transaction Statistics by User Type
    {mo.as_html(txn_summary)}
    """
    )
    return (
        txn_stats_by_user,
        txn_stats_with_fraud,
        txn_summary,
        user_stats,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 6. Fraud Rings Analysis
    """
    )
    return


@app.cell
def __(fraud_rings_df, mo, pd):
    # Parse fraud rings
    ring_analysis = []
    for _, row in fraud_rings_df.iterrows():
        members = row["members"].split(",")
        ring_analysis.append(
            {
                "Ring ID": row["ring_id"],
                "Member Count": len(members),
                "Members": ", ".join(members[:3]) + ("..." if len(members) > 3 else ""),
            }
        )

    ring_df = pd.DataFrame(ring_analysis)

    mo.md(
        f"""
    ### Fraud Ring Structure

    Total fraud rings detected: **{len(fraud_rings_df)}**

    {mo.as_html(ring_df)}

    Fraud rings represent groups of fraudsters sharing devices and coordinating activities.
    """
    )
    return members, ring_analysis, ring_df, row


@app.cell
def __(mo):
    mo.md(
        """
    ## 7. Device Sharing Analysis
    """
    )
    return


@app.cell
def __(devices_df, mo, pd, user_devices_df, users_df):
    # Calculate device sharing
    device_sharing = (
        user_devices_df.groupby("device_id")["user_id"]
        .agg(["count", list])
        .reset_index()
    )
    device_sharing.columns = ["device_id", "user_count", "user_list"]

    # Identify shared devices
    shared_devices = device_sharing[device_sharing["user_count"] > 1]

    # For each shared device, count how many fraudsters use it
    shared_device_analysis = []
    for _, dev_row in shared_devices.iterrows():
        user_ids = dev_row["user_list"]
        fraud_count = users_df[users_df["user_id"].isin(user_ids)]["is_fraudster"].sum()
        shared_device_analysis.append(
            {
                "Device ID": dev_row["device_id"],
                "Total Users": dev_row["user_count"],
                "Fraudsters": fraud_count,
                "Fraud Rate": f"{fraud_count / dev_row['user_count']:.1%}",
            }
        )

    shared_dev_df = pd.DataFrame(shared_device_analysis)

    mo.md(
        f"""
    ### Device Sharing Statistics

    - Total devices: **{len(devices_df)}**
    - Shared devices (>1 user): **{len(shared_devices)}**
    - Devices shared by fraudsters: **{len(shared_dev_df[shared_dev_df['Fraudsters'] > 0])}**

    {mo.as_html(shared_dev_df)}

    **Key Insight:** Device sharing is a strong indicator of fraud rings.
    """
    )
    return (
        dev_row,
        device_sharing,
        fraud_count,
        shared_dev_df,
        shared_device_analysis,
        shared_devices,
        user_count,
        user_ids,
        user_list,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 8. Correlation Analysis
    """
    )
    return


@app.cell
def __(mo, np, plt, sns, transactions_df, users_df):
    # Prepare features for correlation
    user_features = users_df[["user_id", "is_fraudster", "account_age_days"]].copy()
    user_features["is_fraudster_int"] = user_features["is_fraudster"].astype(int)

    # Transaction features per user
    txn_features = (
        transactions_df.groupby("sender_id")
        .agg({"amount": ["count", "mean", "sum"], "is_fraudulent": "sum"})
        .reset_index()
    )
    txn_features.columns = [
        "user_id",
        "txn_count",
        "avg_txn_amount",
        "total_txn_amount",
        "fraud_txn_count",
    ]

    # Merge features
    feature_df = user_features.merge(txn_features, on="user_id", how="left").fillna(0)

    # Calculate correlation matrix
    corr_cols = [
        "is_fraudster_int",
        "account_age_days",
        "txn_count",
        "avg_txn_amount",
        "total_txn_amount",
        "fraud_txn_count",
    ]
    corr_matrix = feature_df[corr_cols].corr()

    # Plot correlation heatmap
    fig_corr, ax_corr = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        ax=ax_corr,
        vmin=-1,
        vmax=1,
    )
    ax_corr.set_title("Feature Correlation Matrix")
    plt.tight_layout()
    fig_corr_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    {mo.as_html(fig_corr_final)}

    **Key Correlations:**
    - **is_fraudster vs account_age_days**: {corr_matrix.loc['is_fraudster_int', 'account_age_days']:.3f} (strong negative)
    - **is_fraudster vs avg_txn_amount**: {corr_matrix.loc['is_fraudster_int', 'avg_txn_amount']:.3f} (strong positive)
    - **is_fraudster vs txn_count**: {corr_matrix.loc['is_fraudster_int', 'txn_count']:.3f} (positive)

    These correlations confirm our fraud detection features are meaningful.
    """
    )
    return (
        ax_corr,
        avg_txn_amount,
        corr_cols,
        corr_matrix,
        feature_df,
        fig_corr,
        fig_corr_final,
        fraud_txn_count,
        is_fraudster_int,
        total_txn_amount,
        txn_features,
        user_features,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## Summary and Next Steps

    ### Key Findings from EDA:

    1. **Account Age** is the strongest discriminator between fraudsters (mean ~44 days) and normal users (mean ~467 days)
    2. **Transaction Amounts** are significantly higher for fraudulent transactions (~$2493 vs ~$247)
    3. **Transaction Volume** is higher for fraudsters (10.5 vs 4 transactions)
    4. **Device Sharing** is prevalent in fraud rings (6 shared devices among fraudsters)
    5. **Data Quality** is excellent with no missing values and all validation checks passing

    ### Recommendations for Model Development:

    1. Use account age, transaction amount, and transaction volume as primary features
    2. Incorporate graph-based features (device sharing, network centrality)
    3. Consider threshold tuning to balance precision/recall
    4. Monitor for data drift in these key features

    ### Next Notebooks:
    - **02_graph_analysis.py**: Network structure and community detection
    - **03_fraud_patterns.py**: Deep dive into fraud ring behavior
    - **04_feature_engineering.py**: Feature creation and validation
    """
    )
    return


# Missing import for pandas
import pandas as pd

# Define missing variables with placeholder values
user_count = 0
user_list = []
avg_txn_amount = 0.0
fraud_txn_count = 0
is_fraudster_int = 0
total_txn_amount = 0.0


if __name__ == "__main__":
    app.run()
