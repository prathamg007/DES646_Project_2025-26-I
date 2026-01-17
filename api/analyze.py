from final import analyze_text, analyze_text_sentencewise
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    source = data.get("source_text", "")
    candidate = data.get("candidate_text", "")
    result = analyze_text_sentencewise(source, candidate)
    return jsonify({"analysis": result})

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
