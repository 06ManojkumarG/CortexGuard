import joblib
import pandas as pd


CURRENT_MODEL_PATH = (
    "ai/models/cortexguard_decision_tree.joblib"
)

FUTURE_MODEL_PATH = (
    "ai/models/"
    "cortexguard_future_risk_random_forest.joblib"
)


class AIEngine:
    def __init__(self):
        self.current_model_package = joblib.load(
            CURRENT_MODEL_PATH
        )

        self.future_model_package = joblib.load(
            FUTURE_MODEL_PATH
        )

        self.current_model = (
            self.current_model_package["model"]
        )

        self.current_features = (
            self.current_model_package["features"]
        )

        self.future_model = (
            self.future_model_package["model"]
        )

        self.future_features = (
            self.future_model_package["features"]
        )
    def predict_current(self, sample):
        sample_df = pd.DataFrame(
            [sample],
            columns=self.current_features,
        )

        prediction = self.current_model.predict(
            sample_df
        )[0]

        probabilities = self.current_model.predict_proba(
            sample_df
        )[0]

        probability_map = dict(
            zip(
                self.current_model.classes_,
                probabilities,
            )
        )

        return {
            "prediction": prediction,
            "probabilities": probability_map,
        }

    def predict_future(self, window_features):
        sample_df = pd.DataFrame(
            [window_features],
            columns=self.future_features,
        )

        prediction = self.future_model.predict(
            sample_df
        )[0]

        probabilities = self.future_model.predict_proba(
            sample_df
        )[0]

        probability_map = dict(
            zip(
                self.future_model.classes_,
                probabilities,
            )
        )

        return {
            "prediction": prediction,
            "probabilities": probability_map,
        }