
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# Count HTTP requests
REQUEST_COUNT = Counter(
    "flask_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# Measure HTTP request duration
REQUEST_LATENCY = Histogram(
    "flask_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"]
)


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_metrics(response):
    endpoint = request.url_rule.rule if request.url_rule else "unknown"

    REQUEST_COUNT.labels(
        request.method,
        endpoint,
        response.status_code
    ).inc()

    elapsed = time.time() - request.start_time
    REQUEST_LATENCY.labels(endpoint).observe(elapsed)

    return response


@app.route("/")
def home():
    return "Hello! My first DevOps project is running."


@app.route("/health")
def health():
    return jsonify(status="healthy")


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
