import random


class TelemetrySimulator:
    def __init__(self):
        self.mode = "NORMAL"

    def set_mode(self, mode):
        self.mode = mode

    def generate_sample(self):

        if self.mode == "NORMAL":
            return {
                "cpu": random.randint(20, 65),
                "ram": random.randint(30, 65),
                "stack": random.randint(20, 60),
                "heap": random.randint(25, 55),
                "temperature": random.randint(35, 55),
                "current": round(random.uniform(1.0, 2.5), 2),
                "speed": random.randint(1400, 1600),
            }

        elif self.mode == "CPU_FAULT":
            return {
                "cpu": random.randint(80, 98),
                "ram": random.randint(30, 65),
                "stack": random.randint(20, 60),
                "heap": random.randint(25, 55),
                "temperature": random.randint(45, 65),
                "current": round(random.uniform(1.5, 3.0), 2),
                "speed": random.randint(1350, 1600),
            }

        elif self.mode == "MEMORY_FAULT":
            return {
                "cpu": random.randint(20, 65),
                "ram": random.randint(80, 98),
                "stack": random.randint(20, 60),
                "heap": random.randint(25, 55),
                "temperature": random.randint(35, 60),
                "current": round(random.uniform(1.0, 2.7), 2),
                "speed": random.randint(1380, 1600),
            }

        elif self.mode == "STACK_FAULT":
            return {
                "cpu": random.randint(20, 65),
                "ram": random.randint(30, 65),
                "stack": random.randint(80, 98),
                "heap": random.randint(25, 55),
                "temperature": random.randint(35, 60),
                "current": round(random.uniform(1.0, 2.7), 2),
                "speed": random.randint(1380, 1600),
            }

        else:
            return {
                "cpu": 0,
                "ram": 0,
                "stack": 0,
                "heap": 0,
                "temperature": 0,
                "current": 0.0,
                "speed": 0,
            }