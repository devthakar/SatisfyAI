let mediaRecorder;
let audioChunks = [];

document.getElementById('recordButton').addEventListener('click', function() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        this.textContent = "Record";
        console.log("Recording stopped...");
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.addEventListener("dataavailable", event => {
                    audioChunks.push(event.data);
                    console.log('Collecting data...');
                });

                mediaRecorder.addEventListener("stop", () => {
                    console.log("Recording stopped. Preparing to send audio file to server...");
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.readAsArrayBuffer(audioBlob);
                    reader.onloadend = function() {
                        const arrayBuffer = reader.result;
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
                            const wavBuffer = encodeWAV(audioBuffer);
                            const properWavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                            const formData = new FormData();
                            formData.append("audioFile", properWavBlob, "recorded_audio.wav");
                            console.log("Sending audio file to server...");
                            fetch("/upload", {
                                method: "POST",
                                body: formData
                            })
                            .then(response => {
                                console.log("Server response received.");
                                return response.json();
                            })
                            .then(data => {
                                console.log("Server response data:", data);
                            })
                            .catch(error => {
                                console.error("Error uploading:", error);
                            });
                        }, (error) => {
                            console.error("Error decoding audio data:", error);
                        });
                    };
                });

                mediaRecorder.start();
                this.textContent = "Stop Recording";
                console.log("Recording started...");
            })
            .catch(error => {
                console.error("Error accessing the microphone:", error);
            });
    }
});

function encodeWAV(audioBuffer) {
    const sampleRate = audioBuffer.sampleRate; 
    const numChannels = audioBuffer.numberOfChannels;
    const samples = audioBuffer.getChannelData(0);
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); 
    view.setUint16(20, 1, true); 
    view.setUint16(22, numChannels, true); 
    view.setUint32(24, sampleRate, true); 
    view.setUint32(28, sampleRate * numChannels * 16 / 8, true); 
    view.setUint16(32, numChannels * 16 / 8, true); 
    view.setUint16(34, 16, true); 
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);
    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
        const s = Math.max(-1, Math.min(1, samples[i])); 
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true); 
        offset += 2;
    }
    return buffer;
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}
