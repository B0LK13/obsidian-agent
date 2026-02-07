# Speaker Diarization - Implementation Plan

**GitHub Issue**: [#108 - Speaker Diarization](https://github.com/B0LK13/obsidian-agent/issues/108)  
**Priority**: Low 🟢  
**Target Version**: v2.5  
**Status**: 🔬 Research & Planning

---

## Overview

Add **speaker diarization** (who spoke when) to enable better transcription and organization of meeting notes, interviews, and podcasts within Obsidian.

### What is Speaker Diarization?

Speaker diarization answers: **"Who spoke when?"**
- Segments audio by speaker changes
- Labels each segment with speaker ID (Speaker 1, Speaker 2, etc.)
- Enables speaker-specific notes and analysis

**Example Output**:
```
[00:00 - 00:15] Speaker 1: "Let's discuss the quarterly results..."
[00:15 - 00:42] Speaker 2: "Revenue is up 15% compared to..."
[00:42 - 01:03] Speaker 1: "That's great news. What about costs?"
```

---

## Use Cases

### 1. Meeting Notes
```markdown
# Weekly Team Meeting - 2024-01-15

## Participants
- **Speaker 1**: Alice (Product Manager)
- **Speaker 2**: Bob (Engineer)
- **Speaker 3**: Carol (Designer)

## Discussion

### Project Timeline
**Alice** (00:30): We need to ship by end of Q1.
**Bob** (00:45): That's aggressive. Can we scope down?
**Alice** (01:15): What's the minimum viable version?

## Action Items
- [ ] **Bob**: Reduce scope proposal by Friday
- [ ] **Carol**: Mockups for MVP by Wednesday
```

### 2. Interview Transcripts
```markdown
# User Interview #12 - 2024-01-15

**Interviewer**: Can you describe your workflow?
**Participant**: I usually start by reviewing emails...

## Key Insights
- Participant spends 2 hours/day on email (mentioned 3 times)
- Frustrated with current tool (strong language at 15:30)
```

### 3. Podcast Notes
```markdown
# Podcast: AI in 2024 - Episode 42

**Host**: Welcome! Today we're discussing...
**Guest** (Dr. Smith): Thanks for having me.

## Highlights
- **15:30** - Dr. Smith on GPT-4 limitations
- **32:00** - Debate on AI safety regulations
```

---

## Technical Architecture

### Component Overview

```
┌────────────────────────────────────────────────────┐
│             Audio Processing Pipeline               │
├────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│  │  Audio   │───▶│ Speaker  │───▶│  Speech  │    │
│  │  Input   │    │Diarization│   │   to     │    │
│  │  (MP3,   │    │          │    │  Text    │    │
│  │   WAV)   │    │(pyannote)│    │(Whisper) │    │
│  └──────────┘    └──────────┘    └──────────┘    │
│         │               │               │         │
│         │               │               │         │
│         ▼               ▼               ▼         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │Pre-process│   │ Segments │    │Attributed│   │
│  │ & Convert│    │  with    │    │Transcript│   │
│  │          │    │ Speaker  │    │          │   │
│  │          │    │  Labels  │    │(Markdown)│   │
│  └──────────┘    └──────────┘    └──────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Tech Stack

**Speaker Diarization**:
- **pyannote.audio** (Recommended) - State-of-the-art, pretrained models
- Alternative: resemblyzer, speechbrain

**Speech Recognition**:
- **OpenAI Whisper** (Already integrated?) - High accuracy
- Supports 99 languages

**Audio Processing**:
- **pydub** - Audio manipulation
- **librosa** - Audio analysis

---

## Implementation Plan

### Phase 1: Core Diarization (4 weeks)

#### Week 1-2: Setup & Integration

```python
# diarization.py
from pyannote.audio import Pipeline
from typing import List, Tuple, Dict
import torch

class SpeakerDiarizer:
    """Speaker diarization using pyannote.audio."""
    
    def __init__(self, auth_token: str = None):
        """
        Initialize diarization pipeline.
        
        Args:
            auth_token: HuggingFace auth token for model access
        """
        # Load pretrained pipeline
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=auth_token
        )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
    
    def diarize(
        self,
        audio_path: str,
        num_speakers: int = None,
        min_speakers: int = 1,
        max_speakers: int = 10
    ) -> List[Dict]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Fixed number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
        
        Returns:
            List of segments with speaker labels
        """
        # Run diarization
        if num_speakers:
            diarization = self.pipeline(
                audio_path,
                num_speakers=num_speakers
            )
        else:
            diarization = self.pipeline(
                audio_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )
        
        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker,
                'duration': turn.end - turn.start
            })
        
        return segments
    
    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_speaker_stats(self, segments: List[Dict]) -> Dict:
        """Get speaking time statistics per speaker."""
        
        stats = {}
        
        for segment in segments:
            speaker = segment['speaker']
            duration = segment['duration']
            
            if speaker not in stats:
                stats[speaker] = {
                    'total_time': 0.0,
                    'num_turns': 0,
                    'avg_turn_duration': 0.0
                }
            
            stats[speaker]['total_time'] += duration
            stats[speaker]['num_turns'] += 1
        
        # Calculate averages
        for speaker in stats:
            total = stats[speaker]['total_time']
            turns = stats[speaker]['num_turns']
            stats[speaker]['avg_turn_duration'] = total / turns if turns > 0 else 0
        
        return stats
```

**Installation Requirements**:
```python
# requirements-diarization.txt
pyannote.audio==3.1.0
torch>=2.0.0
torchaudio>=2.0.0
pydub>=0.25.1
librosa>=0.10.0
```

**Setup Script**:
```bash
#!/bin/bash
# setup-diarization.sh

echo "Setting up speaker diarization..."

# Install dependencies
pip install -r requirements-diarization.txt

# Accept pyannote.audio terms
echo "Please accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "Then create a HuggingFace access token at: https://huggingface.co/settings/tokens"

# Test installation
python -c "from pyannote.audio import Pipeline; print('✅ Installation successful')"
```

#### Week 3: Transcription Integration

```python
# transcribe_with_speakers.py
import whisper
from diarization import SpeakerDiarizer
from typing import List, Dict
import json

class TranscriberWithSpeakers:
    """Combined transcription and diarization."""
    
    def __init__(self, hf_token: str = None):
        # Load Whisper model
        self.whisper = whisper.load_model("base")  # or "medium", "large"
        
        # Load diarization pipeline
        self.diarizer = SpeakerDiarizer(auth_token=hf_token)
    
    def transcribe(
        self,
        audio_path: str,
        num_speakers: int = None
    ) -> Dict:
        """
        Transcribe audio with speaker labels.
        
        Returns:
            {
                'segments': [...],
                'speaker_stats': {...},
                'full_text': "..."
            }
        """
        print("🎤 Performing speaker diarization...")
        speaker_segments = self.diarizer.diarize(
            audio_path,
            num_speakers=num_speakers
        )
        
        print("📝 Transcribing audio...")
        transcription = self.whisper.transcribe(
            audio_path,
            language='en'  # or auto-detect
        )
        
        print("🔗 Aligning transcription with speakers...")
        aligned_segments = self.align_with_speakers(
            transcription['segments'],
            speaker_segments
        )
        
        # Generate speaker stats
        stats = self.diarizer.get_speaker_stats(speaker_segments)
        
        # Combine full text
        full_text = " ".join([seg['text'] for seg in aligned_segments])
        
        return {
            'segments': aligned_segments,
            'speaker_stats': stats,
            'full_text': full_text
        }
    
    def align_with_speakers(
        self,
        transcription_segments: List[Dict],
        speaker_segments: List[Dict]
    ) -> List[Dict]:
        """
        Align transcription segments with speaker labels.
        
        Uses temporal overlap to assign speakers to text.
        """
        aligned = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg['start']
            trans_end = trans_seg['end']
            trans_mid = (trans_start + trans_end) / 2
            
            # Find speaker at midpoint of transcription segment
            speaker = self.find_speaker_at_time(
                trans_mid,
                speaker_segments
            )
            
            aligned.append({
                'start': trans_start,
                'end': trans_end,
                'speaker': speaker,
                'text': trans_seg['text'].strip()
            })
        
        return aligned
    
    def find_speaker_at_time(
        self,
        time: float,
        speaker_segments: List[Dict]
    ) -> str:
        """Find which speaker is active at a given time."""
        
        for segment in speaker_segments:
            if segment['start'] <= time <= segment['end']:
                return segment['speaker']
        
        # Default if no match
        return "SPEAKER_00"
    
    def export_to_markdown(
        self,
        result: Dict,
        output_path: str,
        title: str = "Transcription"
    ):
        """Export transcription to Markdown format."""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {title}\n\n")
            
            # Speaker stats
            f.write("## Speaker Statistics\n\n")
            for speaker, stats in result['speaker_stats'].items():
                f.write(f"**{speaker}**:\n")
                f.write(f"- Total speaking time: {stats['total_time']:.1f}s\n")
                f.write(f"- Number of turns: {stats['num_turns']}\n")
                f.write(f"- Average turn: {stats['avg_turn_duration']:.1f}s\n\n")
            
            # Transcription
            f.write("## Transcription\n\n")
            
            current_speaker = None
            for segment in result['segments']:
                speaker = segment['speaker']
                timestamp = self.diarizer.format_timestamp(segment['start'])
                text = segment['text']
                
                # Group consecutive segments from same speaker
                if speaker != current_speaker:
                    f.write(f"\n**{speaker}** ({timestamp}): {text}")
                    current_speaker = speaker
                else:
                    f.write(f" {text}")
            
            f.write("\n")
```

**CLI Tool**:
```python
# transcribe_cli.py
import argparse
from transcribe_with_speakers import TranscriberWithSpeakers
import os

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio with speaker diarization"
    )
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument(
        "-o", "--output",
        help="Output markdown file",
        default=None
    )
    parser.add_argument(
        "-s", "--speakers",
        type=int,
        help="Number of speakers (if known)",
        default=None
    )
    parser.add_argument(
        "--hf-token",
        help="HuggingFace token",
        default=os.getenv("HF_TOKEN")
    )
    parser.add_argument(
        "-t", "--title",
        help="Title for transcript",
        default="Transcription"
    )
    
    args = parser.parse_args()
    
    # Default output path
    if args.output is None:
        base = os.path.splitext(args.audio)[0]
        args.output = f"{base}_transcript.md"
    
    # Initialize transcriber
    transcriber = TranscriberWithSpeakers(hf_token=args.hf_token)
    
    # Transcribe
    print(f"Processing {args.audio}...")
    result = transcriber.transcribe(
        args.audio,
        num_speakers=args.speakers
    )
    
    # Export
    transcriber.export_to_markdown(
        result,
        args.output,
        title=args.title
    )
    
    print(f"✅ Transcript saved to {args.output}")

if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Basic usage
python transcribe_cli.py meeting.mp3

# With known number of speakers
python transcribe_cli.py interview.wav -s 2 -t "User Interview #5"

# Custom output
python transcribe_cli.py podcast.mp3 -o notes/podcast_ep42.md
```

#### Week 4: Obsidian Plugin Integration

```typescript
// obsidian-diarization-plugin/main.ts
import { Plugin, TFile, Notice } from 'obsidian';
import { TranscriptionModal } from './modal';

export default class DiarizationPlugin extends Plugin {
    async onload() {
        console.log('Loading Diarization Plugin');
        
        // Add command: Transcribe audio file
        this.addCommand({
            id: 'transcribe-audio',
            name: 'Transcribe Audio with Speakers',
            callback: () => this.showTranscriptionModal()
        });
        
        // Add ribbon icon
        this.addRibbonIcon('microphone', 'Transcribe Audio', () => {
            this.showTranscriptionModal();
        });
    }
    
    async showTranscriptionModal() {
        new TranscriptionModal(this.app, async (audioPath, numSpeakers) => {
            await this.transcribeAudio(audioPath, numSpeakers);
        }).open();
    }
    
    async transcribeAudio(audioPath: string, numSpeakers?: number) {
        new Notice('Starting transcription...');
        
        try {
            // Call Python backend
            const response = await fetch('http://localhost:8765/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    audio_path: audioPath,
                    num_speakers: numSpeakers
                })
            });
            
            const result = await response.json();
            
            // Create markdown note
            await this.createTranscriptNote(result);
            
            new Notice('✅ Transcription complete!');
        } catch (error) {
            new Notice('❌ Transcription failed: ' + error.message);
            console.error(error);
        }
    }
    
    async createTranscriptNote(result: any) {
        const vault = this.app.vault;
        
        // Generate filename
        const filename = `Transcript - ${new Date().toISOString().split('T')[0]}.md`;
        const path = `Transcripts/${filename}`;
        
        // Format content
        let content = `# ${result.title}\n\n`;
        content += `## Metadata\n`;
        content += `- Date: ${new Date().toLocaleString()}\n`;
        content += `- Duration: ${this.formatDuration(result.duration)}\n`;
        content += `- Speakers: ${Object.keys(result.speaker_stats).length}\n\n`;
        
        content += `## Speaker Statistics\n\n`;
        for (const [speaker, stats] of Object.entries(result.speaker_stats)) {
            content += `**${speaker}**:\n`;
            content += `- Speaking time: ${stats.total_time.toFixed(1)}s\n`;
            content += `- Turns: ${stats.num_turns}\n\n`;
        }
        
        content += `## Transcription\n\n`;
        let currentSpeaker = null;
        for (const segment of result.segments) {
            if (segment.speaker !== currentSpeaker) {
                content += `\n**${segment.speaker}** (${this.formatTime(segment.start)}): `;
                currentSpeaker = segment.speaker;
            }
            content += segment.text + ' ';
        }
        
        // Create note
        await vault.create(path, content);
        
        // Open note
        const file = vault.getAbstractFileByPath(path) as TFile;
        await this.app.workspace.getLeaf().openFile(file);
    }
    
    formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatTime(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
```

---

### Phase 2: Advanced Features (4 weeks)

#### Week 5: Speaker Identification

```python
# speaker_identification.py
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
from pathlib import Path

class SpeakerIdentifier:
    """Identify speakers by voice embeddings."""
    
    def __init__(self):
        self.encoder = VoiceEncoder()
        self.known_speakers = {}  # name -> embedding
        self.load_known_speakers()
    
    def load_known_speakers(self):
        """Load known speaker profiles."""
        profile_dir = Path("speaker_profiles")
        
        if not profile_dir.exists():
            return
        
        for profile_path in profile_dir.glob("*.npy"):
            speaker_name = profile_path.stem
            embedding = np.load(profile_path)
            self.known_speakers[speaker_name] = embedding
    
    def create_speaker_profile(
        self,
        name: str,
        audio_samples: List[str]
    ):
        """
        Create speaker profile from audio samples.
        
        Args:
            name: Speaker name
            audio_samples: List of paths to audio files of this speaker
        """
        embeddings = []
        
        for audio_path in audio_samples:
            wav = preprocess_wav(audio_path)
            embedding = self.encoder.embed_utterance(wav)
            embeddings.append(embedding)
        
        # Average embeddings
        speaker_embedding = np.mean(embeddings, axis=0)
        
        # Save profile
        self.known_speakers[name] = speaker_embedding
        profile_path = Path(f"speaker_profiles/{name}.npy")
        profile_path.parent.mkdir(exist_ok=True)
        np.save(profile_path, speaker_embedding)
        
        return speaker_embedding
    
    def identify_speaker(
        self,
        audio_path: str,
        start: float,
        end: float,
        threshold: float = 0.75
    ) -> str:
        """
        Identify speaker in audio segment.
        
        Returns:
            Speaker name if match found, else "UNKNOWN"
        """
        # Extract segment
        wav = preprocess_wav(audio_path)
        sample_rate = 16000
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate)
        segment = wav[start_idx:end_idx]
        
        # Get embedding
        embedding = self.encoder.embed_utterance(segment)
        
        # Compare with known speakers
        best_match = None
        best_similarity = 0.0
        
        for name, known_embedding in self.known_speakers.items():
            similarity = np.dot(embedding, known_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = name
        
        # Return match if above threshold
        if best_similarity >= threshold:
            return best_match
        else:
            return "UNKNOWN"
    
    def label_diarization(
        self,
        audio_path: str,
        segments: List[Dict]
    ) -> List[Dict]:
        """Label diarization segments with speaker names."""
        
        labeled_segments = []
        
        for segment in segments:
            speaker_id = self.identify_speaker(
                audio_path,
                segment['start'],
                segment['end']
            )
            
            labeled_segment = segment.copy()
            labeled_segment['speaker_name'] = speaker_id
            labeled_segments.append(labeled_segment)
        
        return labeled_segments
```

**Usage**:
```python
# Create speaker profiles
identifier = SpeakerIdentifier()

identifier.create_speaker_profile(
    name="Alice",
    audio_samples=[
        "alice_sample1.wav",
        "alice_sample2.wav",
        "alice_sample3.wav"
    ]
)

# Use in transcription
transcriber = TranscriberWithSpeakers()
result = transcriber.transcribe("meeting.mp3")

# Label speakers
identified = identifier.label_diarization(
    "meeting.mp3",
    result['segments']
)

# Now segments have 'speaker_name' field
```

#### Week 6-7: Real-time Processing

```python
# realtime_diarization.py
import pyaudio
import numpy as np
from collections import deque
import threading

class RealtimeDiarizer:
    """Real-time speaker diarization for live audio."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.buffer = deque(maxlen=100)  # 10 seconds at 10 chunks/sec
        self.is_recording = False
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1600  # 0.1 second chunks
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def start_recording(self):
        """Start real-time diarization."""
        self.is_recording = True
        
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        
        self.stream.start_stream()
        
        # Process in background
        self.process_thread = threading.Thread(target=self.process_audio)
        self.process_thread.start()
    
    def stop_recording(self):
        """Stop recording."""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        self.process_thread.join()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio chunks."""
        # Convert to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to buffer
        self.buffer.append(audio_data)
        
        return (in_data, pyaudio.paContinue)
    
    def process_audio(self):
        """Process buffered audio."""
        while self.is_recording:
            if len(self.buffer) < 10:  # Need at least 1 second
                time.sleep(0.1)
                continue
            
            # Get last 3 seconds
            audio_window = np.concatenate(list(self.buffer)[-30:])
            
            # Perform diarization on window
            # (This is simplified - real implementation would be more complex)
            speaker = self.detect_speaker(audio_window)
            
            # Callback with result
            if self.callback:
                self.callback(speaker)
            
            time.sleep(1.0)  # Process every second
    
    def detect_speaker(self, audio: np.ndarray) -> str:
        """Detect active speaker in audio window."""
        # TODO: Implement actual detection
        # Could use VAD + quick embedding comparison
        return "SPEAKER_01"
```

#### Week 8: Batch Processing

```python
# batch_processor.py
from pathlib import Path
from typing import List
import concurrent.futures
from tqdm import tqdm

class BatchTranscriber:
    """Batch process multiple audio files."""
    
    def __init__(self, hf_token: str = None):
        self.transcriber = TranscriberWithSpeakers(hf_token=hf_token)
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str = "*.mp3",
        num_workers: int = 2
    ):
        """
        Process all audio files in directory.
        
        Args:
            input_dir: Directory with audio files
            output_dir: Directory for transcripts
            file_pattern: Glob pattern for audio files
            num_workers: Number of parallel workers
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Find audio files
        audio_files = list(input_path.glob(file_pattern))
        print(f"Found {len(audio_files)} audio files")
        
        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for audio_file in audio_files:
                output_file = output_path / f"{audio_file.stem}_transcript.md"
                
                future = executor.submit(
                    self.process_file,
                    audio_file,
                    output_file
                )
                futures.append(future)
            
            # Wait with progress bar
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Transcribing"
            ):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error: {e}")
    
    def process_file(self, input_path: Path, output_path: Path):
        """Process single file."""
        # Transcribe
        result = self.transcriber.transcribe(str(input_path))
        
        # Export
        self.transcriber.export_to_markdown(
            result,
            str(output_path),
            title=input_path.stem
        )
```

**CLI for Batch**:
```bash
# Batch process directory
python batch_transcribe.py \
    --input ./meetings \
    --output ./transcripts \
    --pattern "*.mp3" \
    --workers 4
```

---

### Phase 3: UI & Polish (2 weeks)

#### Week 9-10: Enhanced Obsidian UI

```typescript
// speaker-editor-view.ts
export class SpeakerEditorView extends ItemView {
    async onOpen() {
        const container = this.containerEl.children[1];
        container.empty();
        
        // Speaker list
        const speakerList = container.createDiv({ cls: 'speaker-list' });
        
        // Load speakers
        const speakers = await this.loadSpeakers();
        
        for (const speaker of speakers) {
            this.renderSpeaker(speakerList, speaker);
        }
        
        // Add speaker button
        const addBtn = container.createEl('button', {
            text: '+ Add Speaker Profile'
        });
        addBtn.onclick = () => this.showAddSpeakerModal();
    }
    
    renderSpeaker(container: HTMLElement, speaker: any) {
        const item = container.createDiv({ cls: 'speaker-item' });
        
        item.createEl('h4', { text: speaker.name });
        item.createEl('p', { 
            text: `${speaker.num_samples} voice samples` 
        });
        
        // Edit button
        const editBtn = item.createEl('button', { text: 'Edit' });
        editBtn.onclick = () => this.editSpeaker(speaker);
        
        // Delete button
        const delBtn = item.createEl('button', { text: 'Delete' });
        delBtn.onclick = () => this.deleteSpeaker(speaker);
    }
}
```

---

## Performance Specifications

### Processing Speed

| Audio Length | Diarization | Transcription | Total | GPU |
|--------------|-------------|---------------|-------|-----|
| **1 minute** | 5s | 3s | 8s | ✓ |
| **10 minutes** | 30s | 20s | 50s | ✓ |
| **1 hour** | 2min | 3min | 5min | ✓ |
| **1 hour** | 8min | 15min | 23min | ✗ |

### Accuracy Targets

- **Diarization Error Rate (DER)**: <10%
- **Word Error Rate (WER)**: <5% (English)
- **Speaker Confusion**: <5%

---

## Cost Analysis

### Computation Costs

**Local Processing**:
- Hardware: GPU recommended (RTX 3060+)
- Cost: $0 (after initial hardware)

**Cloud Processing** (if needed):
- RunPod GPU: $0.40/hour
- 1 hour audio: ~5 min processing = $0.03
- 100 hours/month: ~$3

### Storage

- Audio files: ~1MB/minute
- Transcripts: ~10KB/minute
- Speaker profiles: ~1MB each

---

## Next Steps

1. **Prototype** (4 weeks)
   - Implement core diarization
   - Test accuracy on sample meetings
   - Build basic Obsidian integration

2. **Alpha Testing** (4 weeks)
   - Deploy to 10 beta users
   - Collect feedback on accuracy
   - Refine speaker identification

3. **Full Implementation** (8 weeks)
   - Real-time processing
   - Batch tools
   - Polish UI

4. **Beta Release** (v2.5-beta)

---

**Status**: 🔬 Research Complete  
**Next Action**: Prototype Development  
**Estimated Timeline**: 12-16 weeks to v2.5 beta  
**GitHub Issue**: [#108](https://github.com/B0LK13/obsidian-agent/issues/108)
