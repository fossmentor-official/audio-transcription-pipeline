from audio_loader import AudioFileLoader


class SpeechTranscriber:
    """Converts spoken audio into text using OpenAI Whisper."""

    def __init__(self, model_name="turbo", model=None):
        if model is not None:
            self.model = model
        else:
            import whisper
            self.model = whisper.load_model(model_name)

    def transcribe(self, audio_file):
        audio_file = AudioFileLoader(audio_file).load_audio_file()
        result = self.model.transcribe(str(audio_file), fp16=False)
        text = result.get("text", "").strip()

        if not text:
            raise ValueError("No speech was detected in the audio file")

        return text
