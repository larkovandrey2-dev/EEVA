from sklearn import mixture
from sklearn.preprocessing import MinMaxScaler

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
df = pd.read_csv("master_features_final.csv")
df_print = df.drop(columns=["user_id"])
params = {
    "n_clusters": 7,
    "random_state": 42,
}

X = df_print

X = MinMaxScaler().fit_transform(X)
gmm = mixture.GaussianMixture(
        n_components=params["n_clusters"],
        covariance_type="full",
        random_state=params["random_state"],
    )
gmm.fit(X)
y_pred = gmm.fit_predict(X)