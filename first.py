import time
import os
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor


model_name = "facebook/wav2vec2-base-960h"
processor = Wav2Vec2Processor.from_pretrained(model_name)
model = Wav2Vec2ForCTC.from_pretrained(model_name)

def load_audio(file_path, target_sample_rate=16000):
    waveform, sample_rate = torchaudio.load(file_path)

    if sample_rate != target_sample_rate:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
        waveform = resampler(waveform)
    
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0)
    return waveform

def transcribe_audio(file_path):
    waveform = load_audio(file_path)
    waveform = waveform.squeeze()
    
    inputs = processor(waveform, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    print(f"Transcription for {file_path}: {transcription}")

def watch_directory(directory):
    processed_files = set()
    while True:
        for filename in os.listdir(directory):
            if filename.endswith(".wav") and filename not in processed_files:
                file_path = os.path.join(directory, filename)
                try:
                    transcribe_audio(file_path)
                    processed_files.add(filename)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    watch_directory("uploads")
