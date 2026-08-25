RISK_NORMAL = "NORMAL"
RISK_WARNING = "WARNING"
RISK_HIGH = "HIGH_RISK"


def assign_future_risk(features):
    warning_score = 0
    high_risk_score = 0

    # CPU trend
    if features["cpu_trend"] >= 15:
        warning_score += 1

    if features["cpu_trend"] >= 25:
        high_risk_score += 1

    # RAM trend
    if features["ram_trend"] >= 10:
        warning_score += 1

    if features["ram_trend"] >= 20:
        high_risk_score += 1

    # Heap trend
    if features["heap_trend"] >= 10:
        warning_score += 1

    if features["heap_trend"] >= 20:
        high_risk_score += 1

    # Stack trend
    if features["stack_trend"] >= 10:
        warning_score += 1

    if features["stack_trend"] >= 20:
        high_risk_score += 1

    # Temperature trend
    if features["temperature_trend"] >= 5:
        warning_score += 1

    if features["temperature_trend"] >= 10:
        high_risk_score += 1

    # Current trend
    if features["current_trend"] >= 0.5:
        warning_score += 1

    if features["current_trend"] >= 1.0:
        high_risk_score += 1

    # Falling speed can indicate degradation
    if features["speed_trend"] <= -100:
        warning_score += 1

    if features["speed_trend"] <= -200:
        high_risk_score += 1

    if high_risk_score >= 2:
        return RISK_HIGH

    if warning_score >= 2:
        return RISK_WARNING

    return RISK_NORMAL