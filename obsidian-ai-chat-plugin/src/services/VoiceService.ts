import { Notice } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export interface VoiceRecording {
	id: string;
	blob: Blob;
	duration: number;
	timestamp: number;
	transcription?: string;
}

export class VoiceService {
	plugin: AIChatNotesPlugin;
	mediaRecorder: MediaRecorder | null = null;
	audioChunks: Blob[] = [];
	isRecording: boolean = false;
	recordingStartTime: number = 0;
	private stream: MediaStream | null = null;

	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
	}

	async startRecording(): Promise<boolean> {
		try {
			this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			this.mediaRecorder = new MediaRecorder(this.stream);
			this.audioChunks = [];

			this.mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					this.audioChunks.push(event.data);
				}
			};

			this.mediaRecorder.start();
			this.isRecording = true;
			this.recordingStartTime = Date.now();
			
			new Notice('🎙️ Recording started...');
			return true;
		} catch (error) {
			console.error('Failed to start recording:', error);
			new Notice('❌ Failed to access microphone. Please check permissions.');
			return false;
		}
	}

	stopRecording(): Promise<VoiceRecording | null> {
		return new Promise((resolve) => {
			if (!this.mediaRecorder || !this.isRecording) {
				resolve(null);
				return;
			}

			const duration = Date.now() - this.recordingStartTime;

			this.mediaRecorder.onstop = () => {
				const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
				
				// Stop all tracks
				this.stream?.getTracks().forEach(track => track.stop());
				
				const recording: VoiceRecording = {
					id: crypto.randomUUID(),
					blob: audioBlob,
					duration,
					timestamp: Date.now()
				};

				this.isRecording = false;
				this.audioChunks = [];
				
				new Notice(`✅ Recording saved (${Math.round(duration / 1000)}s)`);
				resolve(recording);
			};

			this.mediaRecorder.stop();
		});
	}

	cancelRecording() {
		if (this.mediaRecorder && this.isRecording) {
			this.mediaRecorder.stop();
			this.stream?.getTracks().forEach(track => track.stop());
			this.isRecording = false;
			this.audioChunks = [];
			new Notice('Recording cancelled');
		}
	}

	async transcribeRecording(recording: VoiceRecording): Promise<string> {
		try {
			// Convert blob to base64
			const base64Audio = await this.blobToBase64(recording.blob);
			
			// Use OpenAI Whisper API if available
			if (this.plugin.settings.openaiApiKey) {
				return await this.transcribeWithWhisper(base64Audio);
			}
			
			// Fallback: Use Ollama for transcription if it supports audio
			// For now, we'll use a placeholder that instructs the user
			new Notice('⚠️ Using OpenAI for transcription. Add API key in settings.');
			return '[Audio message - transcription requires OpenAI API key]';
		} catch (error) {
			console.error('Transcription error:', error);
			return '[Transcription failed]';
		}
	}

	private async transcribeWithWhisper(base64Audio: string): Promise<string> {
		// Remove data URL prefix if present
		const base64Data = base64Audio.split(',')[1] || base64Audio;
		
		// Convert base64 to blob for FormData
		const byteCharacters = atob(base64Data);
		const byteNumbers = new Array(byteCharacters.length);
		for (let i = 0; i < byteCharacters.length; i++) {
			byteNumbers[i] = byteCharacters.charCodeAt(i);
		}
		const byteArray = new Uint8Array(byteNumbers);
		const blob = new Blob([byteArray], { type: 'audio/webm' });

		const formData = new FormData();
		formData.append('file', blob, 'recording.webm');
		formData.append('model', 'whisper-1');

		const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${this.plugin.settings.openaiApiKey}`
			},
			body: formData
		});

		if (!response.ok) {
			throw new Error(`Transcription failed: ${response.statusText}`);
		}

		const data = await response.json();
		return data.text;
	}

	private blobToBase64(blob: Blob): Promise<string> {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onloadend = () => resolve(reader.result as string);
			reader.onerror = reject;
			reader.readAsDataURL(blob);
		});
	}

	createAudioUrl(recording: VoiceRecording): string {
		return URL.createObjectURL(recording.blob);
	}

	formatDuration(ms: number): string {
		const seconds = Math.floor(ms / 1000);
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	downloadRecording(recording: VoiceRecording, filename?: string) {
		const url = this.createAudioUrl(recording);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename || `voice-message-${recording.id}.webm`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
}
