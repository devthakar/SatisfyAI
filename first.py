from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import os
import tempfile
import google.generativeai as genai

# blank regarding posting on public repo 
genai.configure(api_key="")

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 0,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = ''
db = SQLAlchemy(app)

print(f"Connected to database: {app.config['SQLALCHEMY_DATABASE_URI']}")

model_name = "facebook/wav2vec2-base-960h"
processor = Wav2Vec2Processor.from_pretrained(model_name)
transcription_model = Wav2Vec2ForCTC.from_pretrained(model_name)

class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)

def load_audio(file_path, target_sample_rate=16000):
    waveform, sample_rate = torchaudio.load(file_path)
    if sample_rate != target_sample_rate:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
        waveform = resampler(waveform)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0)
    return waveform

def transcribe_audio(audio_file):
    with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
        audio_file.save(temp_audio_file)
        temp_audio_file_path = temp_audio_file.name

    waveform = load_audio(temp_audio_file_path)
    waveform = waveform.squeeze()
    inputs = processor(waveform, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = transcription_model(inputs.input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]

    os.remove(temp_audio_file_path)  
    return transcription

def generate_insights(transcriptions):
    combined_text = " ".join(transcriptions)
    prompt = f"Based on these reviews generate insights and suggestions for how to improve my business, but keep it concise and just give bullet points: {combined_text}"

    response = model.generate_content(prompt)
    insights = response.text
    formatted_insights = insights.replace('\n\n', '<br><br>')  
    formatted_insights = formatted_insights.replace('•', '&bull;')  

    return formatted_insights

@app.route('/userrecording')
def home():
    return render_template('home.html')

@app.route('/records')
def records():
    return render_template('records.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'audioFile' in request.files and 'name' in request.form:
            audio_file = request.files['audioFile']
            name = request.form['name']
            date = request.form['date']
            print(f"Received file: {audio_file.filename}, name: {name}, date: {date}")
            transcription = transcribe_audio(audio_file)
            new_transcription = Transcription(name=name, date=date, text=transcription)
            db.session.add(new_transcription)
            db.session.commit()
            print(f"Transcription saved to database: name={name}, date={date}, text={transcription}")
            return jsonify({'transcription': transcription}), 200
        return jsonify({'error': 'No file provided'}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/Transcriptions', methods=['GET'])
def get_transcriptions():
    transcriptions = Transcription.query.all()
    return jsonify({'transcriptions': [{'name': t.name, 'date': t.date, 'text': t.text} for t in transcriptions]})

@app.route('/insights')
def insights():
    return render_template('insights.html')

@app.route('/generate-insights', methods=['GET'])
def generate_insights_route():
    try:
        transcriptions = [t.text for t in Transcription.query.all()]
        insights = generate_insights(transcriptions)
        return jsonify({'insights': insights})
    except Exception as e:
        print(f"Error generating insights: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
