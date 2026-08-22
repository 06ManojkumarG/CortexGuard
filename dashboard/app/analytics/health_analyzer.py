class HealthAnalyzer:

    def analyze(self, sample):
        cpu = sample["cpu"]
        ram = sample["ram"]
        stack = sample["stack"]

        alerts = []

        # CPU analysis
        if cpu >= 90:
            alerts.append("CRITICAL: CPU usage is extremely high")
        elif cpu >= 75:
            alerts.append("WARNING: CPU usage is high")

        # RAM analysis
        if ram >= 90:
            alerts.append("CRITICAL: RAM usage is extremely high")
        elif ram >= 75:
            alerts.append("WARNING: RAM usage is high")

        # Stack analysis
        if stack >= 90:
            alerts.append("CRITICAL: Stack usage is extremely high")
        elif stack >= 75:
            alerts.append("WARNING: Stack usage is high")

        # Overall system status
        if any("CRITICAL" in alert for alert in alerts):
            status = "CRITICAL"

        elif any("WARNING" in alert for alert in alerts):
            status = "WARNING"

        else:
            status = "NORMAL"

        return {
            "status": status,
            "alerts": alerts,
        }