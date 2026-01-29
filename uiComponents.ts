/**
 * Enhanced UI Components for Obsidian Agent
 * Implements 2025 Chat Design Patterns
 */

import { Notice, setIcon, setTooltip } from 'obsidian';

// ========================================
// TYPING INDICATOR COMPONENT
// ========================================

export class TypingIndicator {
	private container: HTMLElement;
	private dots: HTMLElement[] = [];

	constructor(parent: HTMLElement) {
		this.container = parent.createDiv({ cls: 'oa-typing-indicator' });
		this.container.createSpan({ text: 'AI is typing', cls: 'oa-sr-only' });
		
		const dotsContainer = this.container.createDiv({ cls: 'oa-typing-indicator__dots' });
		for (let i = 0; i < 3; i++) {
			this.dots.push(dotsContainer.createDiv({ cls: 'oa-typing-indicator__dot' }));
		}
		
		this.hide();
	}

	show() {
		this.container.style.display = 'flex';
	}

	hide() {
		this.container.style.display = 'none';
	}

	destroy() {
		this.container.remove();
	}
}

// ========================================
// MESSAGE REACTIONS COMPONENT
// ========================================

interface Reaction {
	emoji: string;
	count: number;
	userReacted: boolean;
}

export class MessageReactions {
	private container: HTMLElement;
	private reactions: Map<string, Reaction> = new Map();
	private onReactionToggle: (emoji: string) => void;

	constructor(
		parent: HTMLElement,
		onReactionToggle: (emoji: string) => void
	) {
		this.container = parent.createDiv({ cls: 'oa-message__reactions' });
		this.onReactionToggle = onReactionToggle;
		
		// Add reaction button
		const addButton = this.container.createSpan({ 
			cls: 'oa-reaction oa-reaction__add',
			text: '+'
		});
		setTooltip(addButton, 'Add reaction');
		addButton.addEventListener('click', (e) => {
			e.stopPropagation();
			this.showReactionPicker(e);
		});
	}

	addReaction(emoji: string, count: number = 1, userReacted: boolean = false) {
		this.reactions.set(emoji, { emoji, count, userReacted });
		this.render();
	}

	removeReaction(emoji: string) {
		this.reactions.delete(emoji);
		this.render();
	}

	toggleReaction(emoji: string) {
		const existing = this.reactions.get(emoji);
		if (existing) {
			if (existing.userReacted) {
				if (existing.count > 1) {
					this.reactions.set(emoji, {
						...existing,
						count: existing.count - 1,
						userReacted: false
					});
				} else {
					this.reactions.delete(emoji);
				}
			} else {
				this.reactions.set(emoji, {
					...existing,
					count: existing.count + 1,
					userReacted: true
				});
			}
		} else {
			this.reactions.set(emoji, { emoji, count: 1, userReacted: true });
		}
		this.render();
		this.onReactionToggle(emoji);
	}

	private render() {
		// Clear existing reactions (except add button)
		const existingReactions = this.container.querySelectorAll('.oa-reaction:not(.oa-reaction__add)');
		existingReactions.forEach(el => el.remove());

		// Add reactions before the add button
		const addButton = this.container.querySelector('.oa-reaction__add');
		
		this.reactions.forEach((reaction) => {
			const el = document.createElement('span');
			el.className = `oa-reaction ${reaction.userReacted ? 'oa-reaction--active' : ''}`;
			el.innerHTML = `${reaction.emoji} ${reaction.count > 1 ? reaction.count : ''}`;
			setTooltip(el, reaction.userReacted ? 'Remove reaction' : 'Add reaction');
			el.addEventListener('click', (e) => {
				e.stopPropagation();
				this.toggleReaction(reaction.emoji);
			});
			
			if (addButton) {
				this.container.insertBefore(el, addButton);
			} else {
				this.container.appendChild(el);
			}
		});
	}

	private showReactionPicker(e: MouseEvent) {
		const picker = document.createElement('div');
		picker.className = 'oa-reaction-picker';
		picker.style.position = 'absolute';
		picker.style.zIndex = '1000';
		
		const emojis = ['👍', '❤️', '😄', '🎉', '🤔', '👀', '🔥', '✅'];
		emojis.forEach(emoji => {
			const btn = picker.createDiv({ cls: 'oa-reaction-picker__emoji', text: emoji });
			btn.addEventListener('click', () => {
				this.toggleReaction(emoji);
				picker.remove();
			});
		});
		
		document.body.appendChild(picker);
		
		// Position picker
		const rect = (e.target as HTMLElement).getBoundingClientRect();
		picker.style.left = `${rect.left}px`;
		picker.style.top = `${rect.top - picker.offsetHeight - 8}px`;
		
		// Close on outside click
		const closePicker = (ev: MouseEvent) => {
			if (!picker.contains(ev.target as Node)) {
				picker.remove();
				document.removeEventListener('click', closePicker);
			}
		};
		setTimeout(() => document.addEventListener('click', closePicker), 0);
	}

	destroy() {
		this.container.remove();
	}
}

// ========================================
// VOICE MESSAGE COMPONENT
// ========================================

export class VoiceMessagePlayer {
	private container: HTMLElement;
	private playButton: HTMLButtonElement;
	private waveformContainer: HTMLElement;
	private durationEl: HTMLElement;
	private isPlaying: boolean = false;
	private currentTime: number = 0;
	private duration: number;
	private audioData: number[];
	private animationId: number | null = null;

	constructor(
		parent: HTMLElement,
		audioData: number[],
		duration: number, // in seconds
		onPlay?: () => void
	) {
		this.audioData = audioData;
		this.duration = duration;
		
		this.container = parent.createDiv({ cls: 'oa-voice-message' });
		
		// Play button
		this.playButton = this.container.createEl('button', { cls: 'oa-voice-message__play' });
		this.updatePlayIcon();
		this.playButton.addEventListener('click', () => {
			this.togglePlay();
			onPlay?.();
		});
		
		// Waveform
		this.waveformContainer = this.container.createDiv({ cls: 'oa-voice-message__waveform' });
		this.renderWaveform();
		
		// Duration
		this.durationEl = this.container.createDiv({ cls: 'oa-voice-message__duration' });
		this.updateDuration();
	}

	private renderWaveform() {
		this.waveformContainer.empty();
		
		// Generate waveform bars from audio data
		this.audioData.forEach((value, index) => {
			const bar = this.waveformContainer.createDiv({ cls: 'oa-waveform__bar' });
			const height = Math.max(4, value * 28);
			bar.style.height = `${height}px`;
			
			// Add click handler for seeking
			bar.addEventListener('click', () => {
				this.seekTo(index / this.audioData.length);
			});
		});
	}

	private togglePlay() {
		this.isPlaying = !this.isPlaying;
		this.updatePlayIcon();
		
		if (this.isPlaying) {
			this.startPlayback();
		} else {
			this.stopPlayback();
		}
	}

	private startPlayback() {
		const startTime = Date.now() - (this.currentTime * 1000);
		
		const update = () => {
			if (!this.isPlaying) return;
			
			this.currentTime = (Date.now() - startTime) / 1000;
			
			if (this.currentTime >= this.duration) {
				this.currentTime = 0;
				this.isPlaying = false;
				this.updatePlayIcon();
				this.updateWaveform();
				return;
			}
			
			this.updateWaveform();
			this.updateDuration();
			this.animationId = requestAnimationFrame(update);
		};
		
		this.animationId = requestAnimationFrame(update);
	}

	private stopPlayback() {
		if (this.animationId) {
			cancelAnimationFrame(this.animationId);
			this.animationId = null;
		}
	}

	private seekTo(percentage: number) {
		this.currentTime = percentage * this.duration;
		this.updateWaveform();
		this.updateDuration();
	}

	private updateWaveform() {
		const progress = this.currentTime / this.duration;
		const bars = this.waveformContainer.querySelectorAll('.oa-waveform__bar');
		const playedIndex = Math.floor(progress * bars.length);
		
		bars.forEach((bar, index) => {
			bar.classList.toggle('oa-waveform__bar--played', index < playedIndex);
			bar.classList.toggle('oa-waveform__bar--active', this.isPlaying && index === playedIndex);
		});
	}

	private updatePlayIcon() {
		this.playButton.empty();
		const icon = this.isPlaying ? 'pause' : 'play';
		setIcon(this.playButton, icon);
	}

	private updateDuration() {
		const remaining = Math.max(0, this.duration - this.currentTime);
		this.durationEl.textContent = this.formatTime(remaining);
	}

	private formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	destroy() {
		this.stopPlayback();
		this.container.remove();
	}
}

// ========================================
// VOICE RECORDER COMPONENT
// ========================================

export class VoiceRecorder {
	private container: HTMLElement;
	private isRecording: boolean = false;
	private startTime: number = 0;
	private timerInterval: number | null = null;
	private onStop: (duration: number) => void;

	constructor(
		parent: HTMLElement,
		onStop: (duration: number) => void
	) {
		this.onStop = onStop;
		this.container = parent.createDiv({ cls: 'oa-voice-recorder' });
		this.container.style.display = 'none';
		
		this.container.createDiv({ cls: 'oa-voice-recorder__indicator' });
		this.container.createDiv({ text: 'Recording...' });
		this.container.createDiv({ cls: 'oa-voice-recorder__timer' });
		
		const stopBtn = this.container.createEl('button', { 
			text: 'Stop',
			cls: 'oa-button oa-button--danger'
		});
		stopBtn.addEventListener('click', () => this.stop());
	}

	start() {
		this.isRecording = true;
		this.startTime = Date.now();
		this.container.style.display = 'flex';
		
		this.timerInterval = window.setInterval(() => {
			const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
			const timerEl = this.container.querySelector('.oa-voice-recorder__timer');
			if (timerEl) {
				timerEl.textContent = this.formatTime(elapsed);
			}
		}, 1000);
		
		new Notice('Voice recording started');
	}

	stop() {
		if (!this.isRecording) return;
		
		this.isRecording = false;
		const duration = Math.floor((Date.now() - this.startTime) / 1000);
		
		if (this.timerInterval) {
			clearInterval(this.timerInterval);
			this.timerInterval = null;
		}
		
		this.container.style.display = 'none';
		this.onStop(duration);
	}

	private formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	destroy() {
		if (this.timerInterval) {
			clearInterval(this.timerInterval);
		}
		this.container.remove();
	}
}

// ========================================
// SCROLL TO BOTTOM BUTTON
// ========================================

export class ScrollToBottomButton {
	private button: HTMLElement;
	private badge: HTMLElement;
	private unreadCount: number = 0;
	private onClick: () => void;


	constructor(
		parent: HTMLElement,
		scrollContainer: HTMLElement,
		onClick: () => void
	) {
		this.onClick = onClick;
		
		this.button = parent.createEl('button', { cls: 'oa-scroll-bottom' });
		setIcon(this.button, 'arrow-down');
		setTooltip(this.button, 'Scroll to bottom');
		
		this.badge = this.button.createDiv({ cls: 'oa-scroll-bottom__badge' });
		this.badge.style.display = 'none';
		
		this.button.addEventListener('click', () => {
			this.onClick();
			this.hide();
		});
		
		// Hide initially
		this.hide();
		
		// Observe scroll position
		scrollContainer.addEventListener('scroll', () => {
			const isNearBottom = scrollContainer.scrollHeight - scrollContainer.scrollTop - scrollContainer.clientHeight < 100;
			if (isNearBottom) {
				this.hide();
			}
		});
	}

	show() {
		this.button.style.display = 'flex';
	}

	hide() {
		this.button.style.display = 'none';
		this.unreadCount = 0;
		this.updateBadge();
	}

	incrementUnread() {
		this.unreadCount++;
		this.updateBadge();
		this.show();
	}

	private updateBadge() {
		if (this.unreadCount > 0) {
			this.badge.style.display = 'flex';
			this.badge.textContent = this.unreadCount > 99 ? '99+' : String(this.unreadCount);
		} else {
			this.badge.style.display = 'none';
		}
	}

	destroy() {
		this.button.remove();
	}
}

// ========================================
// SEARCH INTERFACE COMPONENT
// ========================================

export interface SearchResult {
	id: string;
	content: string;
	timestamp: number;
	matchRanges: [number, number][];
}

export class SearchInterface {
	private container: HTMLElement;
	private input: HTMLInputElement;
	private resultsContainer: HTMLElement;
	private onSearch: (_query: string) => SearchResult[];
	private onResultClick: (result: SearchResult) => void;

	constructor(
		parent: HTMLElement,
		onSearch: (query: string) => SearchResult[],
		onResultClick: (result: SearchResult) => void
	) {
		this.onSearch = onSearch;
		this.onResultClick = onResultClick;
		
		this.container = parent.createDiv({ cls: 'oa-search-container' });
		
		// Search input
		const inputWrapper = this.container.createDiv({ cls: 'oa-search-input-wrapper' });
		inputWrapper.createSpan({ cls: 'oa-search-icon' });
		setIcon(inputWrapper.querySelector('.oa-search-icon')!, 'search');
		
		this.input = inputWrapper.createEl('input', {
			cls: 'oa-search-input',
			attr: { placeholder: 'Search conversation...', type: 'text' }
		});
		
		const clearBtn = inputWrapper.createEl('button', { cls: 'oa-search-clear' });
		setIcon(clearBtn, 'x');
		clearBtn.addEventListener('click', () => {
			this.input.value = '';
			this.clearResults();
			this.input.focus();
		});
		
		// Results container
		this.resultsContainer = this.container.createDiv({ cls: 'oa-search-results' });
		this.resultsContainer.style.display = 'none';
		
		// Debounced search
		let debounceTimer: number;
		this.input.addEventListener('input', () => {
			clearTimeout(debounceTimer);
			debounceTimer = window.setTimeout(() => {
				this.performSearch();
			}, 300);
		});
		
		// Close on Escape
		this.input.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') {
				this.clearResults();
				this.input.blur();
			}
		});
	}

	private performSearch() {
		const query = this.input.value.trim();
		
		if (!query) {
			this.clearResults();
			return;
		}
		
		const results = this.onSearch(query);
		this.renderResults(results, query);
	}

	private renderResults(results: SearchResult[], _query: string) {
		this.resultsContainer.empty();
		
		if (results.length === 0) {
			this.resultsContainer.createDiv({
				cls: 'oa-search-empty',
				text: 'No results found'
			});
			this.resultsContainer.style.display = 'block';
			return;
		}
		
		results.forEach(result => {
			const el = this.resultsContainer.createDiv({ cls: 'oa-search-result' });
			
			// Highlight matching text
			let content = result.content;
			result.matchRanges.forEach(([start, end]) => {
				const match = content.slice(start, end);
				content = content.slice(0, start) + 
					`<span class="oa-search-result__match">${match}</span>` +
					content.slice(end);
			});
			
			el.innerHTML = content;
			
			const time = new Date(result.timestamp).toLocaleTimeString();
			el.createDiv({ cls: 'oa-search-result__time', text: time });
			
			el.addEventListener('click', () => {
				this.onResultClick(result);
				this.clearResults();
			});
		});
		
		this.resultsContainer.style.display = 'block';
	}

	private clearResults() {
		this.resultsContainer.empty();
		this.resultsContainer.style.display = 'none';
	}

	focus() {
		this.input.focus();
	}

	destroy() {
		this.container.remove();
	}
}

// ========================================
// MESSAGE ACTIONS MENU
// ========================================

export interface MessageAction {
	icon: string;
	label: string;
	onClick: () => void;
}

export class MessageActions {
	private container: HTMLElement;

	constructor(parent: HTMLElement, actions: MessageAction[]) {
		this.container = parent.createDiv({ cls: 'oa-message-actions' });
		
		actions.forEach(action => {
			const btn = this.container.createEl('button', { cls: 'oa-message-action' });
			setIcon(btn, action.icon);
			setTooltip(btn, action.label);
			btn.addEventListener('click', (e) => {
				e.stopPropagation();
				action.onClick();
			});
		});
	}

	destroy() {
		this.container.remove();
	}
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

export function generateMockWaveform(length: number = 50): number[] {
	return Array.from({ length }, () => Math.random() * 0.8 + 0.2);
}

export function highlightMatches(text: string, query: string): string {
	if (!query) return text;
	
	const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
	return text.replace(regex, '<span class="oa-search-result__match">$1</span>');
}

function escapeRegExp(string: string): string {
	return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ========================================
// ANIMATION UTILITIES
// ========================================

export function animateElement(
	element: HTMLElement,
	keyframes: Keyframe[],
	options: KeyframeAnimationOptions
): Animation {
	return element.animate(keyframes, options);
}

export function fadeIn(element: HTMLElement, duration: number = 250) {
	return animateElement(
		element,
		[{ opacity: 0 }, { opacity: 1 }],
		{ duration, easing: 'ease-out', fill: 'forwards' }
	);
}

export function fadeOut(element: HTMLElement, duration: number = 200) {
	return animateElement(
		element,
		[{ opacity: 1 }, { opacity: 0 }],
		{ duration, easing: 'ease-in', fill: 'forwards' }
	);
}

export function slideUp(element: HTMLElement, duration: number = 300) {
	return animateElement(
		element,
		[{ transform: 'translateY(20px)', opacity: 0 }, { transform: 'translateY(0)', opacity: 1 }],
		{ duration, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', fill: 'forwards' }
	);
}
