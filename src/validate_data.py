import pandas as pd
import great_expectations as ge
import sys
import os
from src.logger import logger

def validate_data():
    file_path = "data/raw/iris.csv"
    if not os.path.exists(file_path):
        logger.error(f"Data file not found at {file_path}")
        sys.exit(1)

    df = pd.read_csv(file_path)
    ge_df = ge.from_pandas(df)
    
    logger.info("Initializing Great Expectations Data Schema Validation...")

    # 1. Expect exact columns
    expected_columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'target']
    res = ge_df.expect_table_columns_to_match_ordered_list(expected_columns)
    if not res.success:
        logger.error(f"Column mismatch: Expected {expected_columns}, got {list(df.columns)}")
        sys.exit(1)
    logger.info("✅ Schema Validation: Columns match.")

    # 2. Expect no nulls
    for col in expected_columns:
        res = ge_df.expect_column_values_to_not_be_null(col)
        if not res.success:
            logger.error(f"Null values found in column {col}")
            sys.exit(1)
    logger.info("✅ Data Quality: No missing values detected.")

    logger.info("Great Expectations validation passed successfully! Data is clean.")

if __name__ == "__main__":
    validate_data()
