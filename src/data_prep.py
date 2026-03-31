import pandas as pd
from sklearn.datasets import load_iris
import os


def prepare_data():
    """Load the Iris dataset and save it to the raw data folder."""
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    df['target'] = iris.target

    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/iris.csv', index=False)
    print("Data preparation complete. Saved to data/raw/iris.csv")


if __name__ == "__main__":
    prepare_data()
