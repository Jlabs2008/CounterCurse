import time as t
import os
import moviepy as mp
import pydub as pd
import whisper as w
import json


class ProfanityFilter:
    def __init__(self):
        self.profanity_lists = self.load_profanity_lists()
        self.whisper_model = None

    def load_profanity_lists(self):
        self.profanity_lists = {}
        levels = ["minor", "moderate", "strict"]

        for level in levels:
            try:
                with open(f"Curselist/{level}.txt", "r") as f:
                    self.profanity_lists[level] = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print(f"Error Code: {level}.txt not found")
                self.profanity_lists[level] = []

        return self.profanity_lists
    def load_whisper_model(self, model_size="base"):
        """Load Whisper model for speech recognition"""
        print(f"Loading Whisper model ({model_size})...")
        self.whisper_model = w.load_model(model_size)
        print("Model loaded successfully!")

    def extract_audio(self, video_path):
        """Extract audio from video file"""
        print("Extracting audio from video...")
        video = mp.VideoFileClip(video_path)
        audio_path = "temp_audio.wav"
        video.audio.write_audiofile(audio_path)
        video.close()
        return audio_path

    def transcribe_audio(self, audio_path):
        """Transcribe audio using Whisper with word-level timestamps"""
        print("Transcribing audio...")
        if not self.whisper_model:
            self.load_whisper_model()
        # Timestamps must be set to true, otherwise CENSORSHIP will not work.
        result = self.whisper_model.transcribe(audio_path, word_timestamps=True)
        return result

    def detect_profanity_segments(self, transcription, level="moderate"):
        """Find profanity words and their timestamps"""
        print(f"Detecting profanity (level: {level})...")

        profanity_words = self.profanity_lists.get(level, self.profanity_lists["moderate"])
        bad_segments = []

        # Check each segment
        for segment in transcription["segments"]:
            if "words" in segment:
                for word_info in segment["words"]:
                    word = word_info["word"].lower().strip()
                    # Remove punctuation for comparison
                    clean_word = ''.join(c for c in word if c.isalpha())

                    if clean_word in profanity_words:
                        bad_segments.append({
                            "word": word,
                            "start": word_info["start"],
                            "end": word_info["end"]
                        })
                        print(f"Found: '{word}' at {word_info['start']:.2f}s - {word_info['end']:.2f}s")

        return bad_segments

    def generate_beep_audio(self, duration, sample_rate=44100):
        """Generate a beep sound for given duration"""
        from pydub.generators import Sine

        # Generate 1000Hz beep
        beep = Sine(1000).to_audio_segment(duration=int(duration * 1000))
        return beep

    def apply_censoring(self, audio_path, bad_segments):
        """Replace profanity segments with beeps"""
        print("Applying censoring...")

        # Load original audio
        audio = pd.AudioSegment.from_wav(audio_path)

        # Sort segments by start time (reverse order for easier processing)
        bad_segments.sort(key=lambda x: x["start"], reverse=True)

        # Replace each bad segment with beep
        for segment in bad_segments:
            start_ms = int(segment["start"] * 1000)
            end_ms = int(segment["end"] * 1000)
            duration = (segment["end"] - segment["start"])

            # Generate beep for this duration
            beep = self.generate_beep_audio(duration)

            # Replace the segment
            audio = audio[:start_ms] + beep + audio[end_ms:]

        return audio

    def create_final_video(self, original_video_path, censored_audio, output_path):
        """Combine censored audio with original video"""
        print("Creating final video...")

        # Save censored audio temporarily
        temp_audio_path = "temp_censored_audio.wav"
        censored_audio.export(temp_audio_path, format="wav")

        # Load original video and replace audio
        video = mp.VideoFileClip(original_video_path)
        new_audio = mp.AudioFileClip(temp_audio_path)

        # FIX 1: Use with_audio instead of set_audio
        final_video = video.with_audio(new_audio)
        final_video.write_videofile(output_path)

        # FIX 2: Properly close all clips before cleanup
        video.close()
        new_audio.close()
        final_video.close()

        # Small delay to ensure files are released
        t.sleep(0.1)

        # Now safe to remove temp file
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except PermissionError:
                print(f"Warning: Could not remove {temp_audio_path} - file may still be in use")

    def cleanup_temp_files(self):
        """Remove temporary files"""
        temp_files = ["temp_audio.wav", "temp_censored_audio.wav"]
        for file in temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except PermissionError:
                    print(f"Warning: Could not remove {file} - file may still be in use")

    def process_video(self, input_path, output_path, profanity_level="moderate"):
        """Main processing function"""
        start_time = t.time()

        try:
            print(f"Processing video: {input_path}")
            print(f"Profanity level: {profanity_level}")

            # Step 1: Extract audio
            audio_path = self.extract_audio(input_path)

            # Step 2: Transcribe audio
            transcription = self.transcribe_audio(audio_path)

            # Step 3: Detect profanity
            bad_segments = self.detect_profanity_segments(transcription, profanity_level)

            if not bad_segments:
                print("No profanity detected!")
                # Still cleanup temp files even if no profanity found
                self.cleanup_temp_files()
                return False

            print(f"Found {len(bad_segments)} words to censor")

            # Step 4: Apply censoring
            censored_audio = self.apply_censoring(audio_path, bad_segments)

            # Step 5: Create final video
            self.create_final_video(input_path, censored_audio, output_path)

            # Step 6: Cleanup
            self.cleanup_temp_files()

            elapsed_time = t.time() - start_time
            print(f"Processing complete! Time taken: {elapsed_time:.2f} seconds")
            print(f"Output saved to: {output_path}")

            return True

        except Exception as e:
            print(f"Error processing video: {str(e)}")
            self.cleanup_temp_files()
            return False


