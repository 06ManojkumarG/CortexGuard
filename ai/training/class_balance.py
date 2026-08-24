import pandas as pd
from sklearn.utils.class_weight import compute_class_weight


DATASET_PATH = "datasets/combined_dataset.csv"


df = pd.read_csv(DATASET_PATH)

y = df["label"]

classes = y.unique().to_numpy()
weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=y,
)

class_weights = dict(zip(classes, weights))


print("Class counts:")
print(y.value_counts())

print()
print("Computed class weights:")
print(class_weights)