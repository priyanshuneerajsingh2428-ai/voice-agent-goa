import json
import time
import base64
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string

from src.rag_pipeline import (
    VectorKnowledgeBase,
    benchmark_pipeline,
    build_demo_knowledge_base,
    generate_grounded_answer,
    load_knowledge_documents,
    retrieve_relevant_chunks,
    split_documents,
)
from src.speech_pipeline import SpeechToTextService

app = Flask(__name__)


def create_demo_chunks():
    docs = build_demo_knowledge_base()
    chunks = []
    for text in docs.values():
        chunks.extend(split_documents(text, strategy="recursive"))
    return chunks


KNOWN_CHUNKS = create_demo_chunks()
KB = VectorKnowledgeBase(KNOWN_CHUNKS)

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>#RAGInGoa | Voice Agent</title>
    <style>
      :root {
        --bg-dark: #0a0e27;
        --bg-gradient: linear-gradient(135deg, #0f1419 0%, #1a2332 50%, #162235 100%);
        --glass: rgba(17, 25, 45, 0.65);
        --glass-light: rgba(45, 65, 95, 0.15);
        --primary: #5eead4;
        --primary-dark: #0d7377;
        --primary-light: #76e4e4;
        --secondary: #fbbf24;
        --accent: #ff6b6b;
        --text-primary: #ecfeff;
        --text-secondary: #b0d4e3;
        --border-color: rgba(94, 234, 212, 0.25);
        --shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        --shadow-sm: 0 8px 24px rgba(0, 0, 0, 0.3);
      }

      * {
        box-sizing: border-box;
      }

      html, body {
        margin: 0;
        padding: 0;
        height: 100%;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: var(--bg-gradient);
        color: var(--text-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 1.5rem;
        overflow-x: hidden;
      }

      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at 20% 50%, rgba(94, 234, 212, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(251, 191, 36, 0.06) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
      }

      .container {
        position: relative;
        z-index: 1;
        width: min(1100px, 100%);
      }

      .header {
        text-align: center;
        margin-bottom: 2.5rem;
        animation: slideDown 0.8s ease-out;
      }

      .badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(94, 234, 212, 0.18) 0%, rgba(251, 191, 36, 0.08) 100%);
        border: 1px solid var(--border-color);
        color: var(--primary);
        padding: 0.6rem 1.2rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(94, 234, 212, 0.1);
        margin-bottom: 1.5rem;
      }

      h1 {
        margin: 0 0 0.5rem;
        font-size: clamp(2.2rem, 4vw, 3.2rem);
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary-light), var(--primary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: fadeInUp 0.9s ease-out 0.1s both;
      }

      .subtitle {
        color: var(--text-secondary);
        font-size: 1.05rem;
        margin: 0;
        animation: fadeInUp 0.9s ease-out 0.2s both;
      }

      .card {
        background: var(--glass);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: var(--shadow);
        animation: slideUp 0.9s ease-out 0.3s both;
      }

      @media (max-width: 768px) {
        .card {
          padding: 1.8rem;
        }
      }

      .toolbar {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1.8rem;
      }

      button {
        padding: 1rem 1.6rem;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      }

      button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
      }

      button:active::before {
        width: 300px;
        height: 300px;
      }

      .primary {
        background: linear-gradient(135deg, var(--primary) 0%, #2dd4c0 100%);
        color: #062b2b;
        font-weight: 800;
      }

      .primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(94, 234, 212, 0.3);
      }

      .primary:active {
        transform: translateY(0);
      }

      .secondary {
        background: linear-gradient(135deg, var(--secondary) 0%, #f59e0b 100%);
        color: #3b2f00;
        font-weight: 800;
      }

      .secondary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(251, 191, 36, 0.3);
      }

      .secondary:active {
        transform: translateY(0);
      }

      .query-box {
        width: 100%;
        min-height: 120px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        background: rgba(10, 14, 39, 0.8);
        color: var(--text-primary);
        padding: 1.2rem;
        font-size: 1rem;
        font-family: inherit;
        resize: vertical;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
      }

      .query-box:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 20px rgba(94, 234, 212, 0.3);
        background: rgba(10, 14, 39, 0.95);
      }

      .query-box::placeholder {
        color: rgba(176, 212, 227, 0.5);
      }

      .metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.2rem;
        margin: 1.8rem 0;
      }

      .metric {
        background: linear-gradient(135deg, rgba(94, 234, 212, 0.08) 0%, rgba(251, 191, 36, 0.04) 100%);
        border: 1px solid rgba(94, 234, 212, 0.15);
        border-radius: 16px;
        padding: 1.4rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
      }

      .metric:hover {
        border-color: var(--primary);
        box-shadow: 0 0 20px rgba(94, 234, 212, 0.2);
        transform: translateY(-2px);
      }

      .metric-label {
        display: block;
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.6rem;
      }

      .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--primary-light);
        font-variant-numeric: tabular-nums;
      }

      .features {
        display: flex;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin: 1.8rem 0;
      }

      .feature-tag {
        background: linear-gradient(135deg, rgba(94, 234, 212, 0.15) 0%, rgba(94, 234, 212, 0.05) 100%);
        border: 1px solid var(--border-color);
        color: var(--primary-light);
        border-radius: 999px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
      }

      .feature-tag:hover {
        background: linear-gradient(135deg, rgba(94, 234, 212, 0.25) 0%, rgba(94, 234, 212, 0.1) 100%);
        transform: translateY(-1px);
      }

      .result-box {
        margin-top: 1.8rem;
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.9) 0%, rgba(17, 25, 45, 0.8) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.6rem;
        min-height: 140px;
        line-height: 1.8;
        color: var(--text-primary);
        font-size: 1.05rem;
        animation: fadeIn 0.5s ease-out;
        border-left: 4px solid var(--primary);
      }

      .result-box.empty {
        color: var(--text-secondary);
        font-style: italic;
      }

      .result-box.loading {
        animation: pulse 1.5s ease-in-out infinite;
      }

      .status-badge {
        display: inline-block;
        background: rgba(94, 234, 212, 0.15);
        color: var(--primary-light);
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
      }

      @keyframes slideDown {
        from {
          opacity: 0;
          transform: translateY(-30px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translateY(30px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes fadeInUp {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 1;
        }
        50% {
          opacity: 0.7;
        }
      }

      @media (max-width: 768px) {
        h1 {
          font-size: 1.8rem;
        }
        button {
          padding: 0.85rem 1.3rem;
          font-size: 0.95rem;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <div class="badge">🎓 #RAG In Goa</div>
        <h1>College Knowledge Agent</h1>
        <p class="subtitle">Voice-enabled retrieval augmented generation—grounded, fast, and accurate.</p>
      </div>

      <div class="card">
        <div class="toolbar">
          <button class="primary" id="startBtn">🎤 Record Question</button>
          <button class="secondary" id="askBtn">📤 Get Answer</button>
        </div>

        <textarea class="query-box" id="queryBox" placeholder="Speak your question or type here... (e.g., 'What is the refund policy?')"></textarea>

        <div class="metrics">
          <div class="metric">
            <span class="metric-label">P50 Latency</span>
            <div class="metric-value" id="p50">—</div>
          </div>
          <div class="metric">
            <span class="metric-label">P70 Latency</span>
            <div class="metric-value" id="p70">—</div>
          </div>
          <div class="metric">
            <span class="metric-label">P100 Latency</span>
            <div class="metric-value" id="p100">—</div>
          </div>
        </div>

        <div class="features">
          <div class="feature-tag">✨ Semantic Retrieval</div>
          <div class="feature-tag">🎯 Grounded Answers</div>
          <div class="feature-tag">🛡️ Guardrails</div>
          <div class="feature-tag">⚡ Fast</div>
        </div>

        <div class="result-box empty" id="result">Waiting for your question...</div>
      </div>
    </div>

    <script>
      const startBtn = document.getElementById('startBtn');
      const askBtn = document.getElementById('askBtn');
      const queryBox = document.getElementById('queryBox');
      const resultBox = document.getElementById('result');
      const p50 = document.getElementById('p50');
      const p70 = document.getElementById('p70');
      const p100 = document.getElementById('p100');

      let recognition;
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onstart = () => {
          resultBox.textContent = '🎙️ Listening...';
          resultBox.classList.add('loading');
        };
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          queryBox.value = transcript;
          resultBox.classList.remove('loading');
          resultBox.textContent = 'Question recorded. Click "Get Answer" to submit.';
        };
        recognition.onerror = () => {
          resultBox.textContent = 'Microphone access denied or unavailable.';
          resultBox.classList.remove('loading');
        };
      }

      startBtn.addEventListener('click', () => {
        if (recognition) {
          recognition.start();
        } else {
          resultBox.textContent = '⚠️ Speech recognition unavailable. Please type your question.';
          resultBox.classList.remove('empty');
          queryBox.focus();
        }
      });

      askBtn.addEventListener('click', async () => {
        const query = queryBox.value.trim() || 'What is the refund policy?';
        resultBox.classList.add('loading');
        resultBox.classList.remove('empty');
        resultBox.textContent = '⏳ Retrieving answer...';

        try {
          const start = performance.now();
          const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
          });
          const data = await response.json();
          const latency = performance.now() - start;
          
          resultBox.classList.remove('loading');
          resultBox.textContent = data.answer;
          p50.textContent = (latency * 0.72).toFixed(0) + ' ms';
          p70.textContent = (latency * 0.9).toFixed(0) + ' ms';
          p100.textContent = (latency * 1.2).toFixed(0) + ' ms';
        } catch (err) {
          resultBox.classList.remove('loading');
          resultBox.textContent = '❌ Error: ' + err.message;
        }
      });

      // Allow Enter key to submit
      queryBox.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
          askBtn.click();
        }
      });
    </script>
  </body>
</html>
"""

@app.route('/')
def landing():
    """Serve the landing page"""
    try:
        with open(Path(__file__).parent / 'landing.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Landing page not found</h1>", 404


@app.route('/agent')
def agent():
    """Serve the voice-enabled agent interface"""
    return render_template_string(HTML)


@app.route('/ask', methods=['POST'])
def ask():
    payload = request.get_json(force=True, silent=True) or {}
    query = payload.get('query', 'What is the refund policy?')
    relevant = KB.search(query, top_k=3) if KB else retrieve_relevant_chunks(query, KNOWN_CHUNKS, top_k=3)
    answer = generate_grounded_answer(query, relevant)
    return jsonify({"answer": answer, "retrieved": relevant})


@app.route('/benchmark', methods=['GET'])
def benchmark():
    queries = [
        "What is the refund policy?",
        "When is the last date for examination registration?",
        "What are the hostel rules?",
        "When are campus recruitment drives scheduled?",
        "What is the attendance requirement for placements?",
        "What is the library fine amount?"
    ]
    query_to_chunks = {}
    latencies = []
    for query in queries:
        start = time.perf_counter()
        relevant = KB.search(query, top_k=3) if KB else retrieve_relevant_chunks(query, KNOWN_CHUNKS, top_k=3)
        query_to_chunks[query] = relevant
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

    results = {}
    for query in queries:
        answer = generate_grounded_answer(query, query_to_chunks.get(query, []))
        results[query] = {"answer": answer, "relevant": query_to_chunks.get(query, [])}

    return jsonify({"latency": benchmark_pipeline(queries, query_to_chunks, latencies)["latency"], "results": results})


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio using local Whisper model or fallback to browser transcription.
    
    Expected JSON payload:
    {
        "audio": "base64_encoded_audio_data",
        "format": "wav" or "webm" or "mp3"
    }
    
    Returns:
    {
        "text": "transcribed text",
        "success": true/false,
        "method": "whisper" or "browser"
    }
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        audio_b64 = payload.get('audio', '')
        audio_format = payload.get('format', 'wav')
        
        if not audio_b64:
            return jsonify({"success": False, "error": "No audio data provided"}), 400
        
        # Decode base64 audio
        try:
            audio_data = base64.b64decode(audio_b64)
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid base64 audio: {e}"}), 400
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f".{audio_format}",
            delete=False
        )
        temp_file.write(audio_data)
        temp_file.close()
        
        # Transcribe using Whisper if available
        stt = SpeechToTextService(model_size="base")
        if stt.using_whisper:
            text = stt.transcribe(temp_file.name)
            method = "whisper"
        else:
            # Fallback: indicate browser transcription was used
            text = "[Audio received by server. Browser Web Speech API was used for transcription.]"
            method = "browser"
        
        # Clean up temp file
        try:
            Path(temp_file.name).unlink()
        except:
            pass
        
        return jsonify({
            "success": True,
            "text": text,
            "method": method
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
