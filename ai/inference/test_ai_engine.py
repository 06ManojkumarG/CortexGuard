from ai_engine import AIEngine


engine = AIEngine()

print("AIEngine loaded successfully.")

print(
    "Current model features:",
    len(engine.current_features),
)

print(
    "Future model features:",
    len(engine.future_features),
)