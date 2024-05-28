import assemblyai as aai
from ajb.config.settings import SETTINGS
from ajb.vendor.assembly.client_factory import AssemblyAIClientFactory


class AssemblyAIRepository:
    def __init__(self, client: aai.Client | None = None):
        self.client = client or AssemblyAIClientFactory.get_client()

        self.transcriber = aai.Transcriber(client=self.client)

    def transcribe_audio(
        self, audio_url: str, diarization: bool = False
    ) -> aai.Transcript:
        # Create transcription config
        config = aai.TranscriptionConfig(speaker_labels=diarization)

        # Transcribe the audio
        transcript = self.transcriber.transcribe(audio_url, config=config)

        # Raise an error if transcription fails
        if transcript.error:
            raise ValueError(transcript.error)

        return transcript
