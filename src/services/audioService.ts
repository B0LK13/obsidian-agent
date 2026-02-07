import { TFile, Vault } from 'obsidian';
import { ObsidianAgentSettings } from '../../settings';

export class AudioService {
    constructor(private settings: ObsidianAgentSettings, private vault: Vault) {}

    async transcribe(file: TFile): Promise<string> {
        if (!this.settings.apiKey) {
            throw new Error('OpenAI API key is required for transcription');
        }

        const data = await this.vault.readBinary(file);
        
        // requestUrl doesn't support FormData/Multipart easily in some Obsidian versions
        // But we can try using standard fetch if requestUrl fails or use a trick.
        // For Whisper, we need multipart/form-data.
        
        const formData = new FormData();
        const blob = new Blob([data], { type: file.extension === 'mp3' ? 'audio/mpeg' : 'audio/wav' });
        formData.append('file', blob, `audio.${file.extension}`);
        formData.append('model', 'whisper-1');

        // Standard fetch is safer for multipart in Obsidian environment
        const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.settings.apiKey}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(`Transcription failed: ${response.status} - ${error}`);
        }

        const result = await response.json();
        return result.text;
    }
}
