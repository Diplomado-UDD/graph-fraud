"""
Data generation script for fraud detection pipeline
Generates synthetic fraud dataset and versions with DVC
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
import config
from src.data.generate_dataset import FraudDatasetGenerator


def generate_and_save_dataset():
    """Generate synthetic fraud dataset and save with versioning"""
    print("=== Fraud Detection Data Generation ===\n")
    print("Configuration:")
    print(f"  Seed: {config.SEED}")
    print(f"  N Users: {config.N_USERS}")
    print(f"  N Transactions: {config.N_TRANSACTIONS}")
    print(f"  Fraud Rate: {config.FRAUD_RATE}")
    print(f"  Data Version: {config.DATA_VERSION}\n")

    # Generate dataset
    print("Generating synthetic dataset...")
    generator = FraudDatasetGenerator(seed=config.SEED)
    dataset = generator.generate_dataset(
        n_users=config.N_USERS, n_transactions=config.N_TRANSACTIONS
    )

    # Save to CSV files
    print(f"\nSaving dataset to {config.RAW_DATA_DIR}/...")
    for name, df in dataset.items():
        output_path = config.RAW_DATA_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"  Saved {name}.csv: {len(df)} records")

    # Create dataset metadata
    metadata = {
        "version": config.DATA_VERSION,
        "generated_at": datetime.now().isoformat(),
        "parameters": {
            "seed": config.SEED,
            "n_users": config.N_USERS,
            "n_transactions": config.N_TRANSACTIONS,
            "fraud_rate": config.FRAUD_RATE,
        },
        "statistics": {
            "users": len(dataset["users"]),
            "fraudsters": int(dataset["users"]["is_fraudster"].sum()),
            "devices": len(dataset["devices"]),
            "transactions": len(dataset["transactions"]),
            "fraudulent_transactions": int(
                dataset["transactions"]["is_fraudulent"].sum()
            ),
            "fraud_rings": len(dataset["fraud_rings"]),
        },
    }

    metadata_path = config.RAW_DATA_DIR / "dataset_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n  Saved metadata: {metadata_path}")

    # Data quality checks
    print("\n=== Data Quality Checks ===")
    print(
        f"  Fraud rate: {metadata['statistics']['fraudsters'] / metadata['statistics']['users']:.1%}"
    )
    print(
        f"  Transaction fraud rate: {metadata['statistics']['fraudulent_transactions'] / metadata['statistics']['transactions']:.1%}"
    )
    print(f"  Fraud rings: {metadata['statistics']['fraud_rings']}")

    # Check for data quality issues
    issues = []
    if metadata["statistics"]["fraudsters"] < config.N_USERS * 0.1:
        issues.append("WARNING: Fraud rate below 10%")
    if dataset["transactions"]["amount"].min() <= 0:
        issues.append("ERROR: Negative or zero transaction amounts found")
    if dataset["users"]["account_age_days"].min() <= 0:
        issues.append("ERROR: Negative or zero account ages found")

    if issues:
        print("\n  Quality Issues Detected:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  All quality checks passed")

    print("\n=== Dataset generation complete ===")
    print("\nNext steps:")
    print("  1. Track with DVC: dvc add data/raw/")
    print(
        f"  2. Commit changes: git add data/raw.dvc && git commit -m 'data: update dataset {config.DATA_VERSION}'"
    )
    print(f"  3. Tag version: git tag data-{config.DATA_VERSION}")

    return dataset, metadata


if __name__ == "__main__":
    dataset, metadata = generate_and_save_dataset()
