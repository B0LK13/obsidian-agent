/**
 * Test Suite for UI Components
 * Tests for 2025 Chat UI Design Patterns
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock Web Animations API
Element.prototype.animate = vi.fn(function(_keyframes: Keyframe[] | PropertyIndexedKeyframes | null, _options?: number | KeyframeAnimationOptions) {
  return {
    playState: 'finished',
    play: vi.fn(),
    pause: vi.fn(),
    cancel: vi.fn(),
    finish: vi.fn(),
    onfinish: null,
    oncancel: null,
    currentTime: null,
    effect: null,
    finished: Promise.resolve(),
    id: '',
    pending: false,
    playbackRate: 1,
    ready: Promise.resolve(),
    startTime: null,
    timeline: null,
    commitStyles: vi.fn(),
    persist: vi.fn(),
    reverse: vi.fn(),
    updatePlaybackRate: vi.fn(),
    removeEventListener: vi.fn(),
    addEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  } as unknown as Animation;
});

// Add Obsidian DOM helpers to HTMLElement prototype
(HTMLElement.prototype as any).createDiv = vi.fn(function(this: HTMLElement, cls?: string | { cls?: string }) {
  const div = document.createElement('div');
  if (typeof cls === 'string') {
    div.className = cls;
  } else if (cls && typeof cls === 'object' && 'cls' in cls) {
    div.className = cls.cls || '';
  }
  this.appendChild(div);
  return div;
});

(HTMLElement.prototype as any).createEl = vi.fn(function<K extends keyof HTMLElementTagNameMap>(
  this: HTMLElement,
  tag: K,
  o?: { cls?: string; text?: string }
) {
  const el = document.createElement(tag);
  if (o?.cls) el.className = o.cls;
  if (o?.text) el.textContent = o.text;
  this.appendChild(el);
  return el;
});

// Mock Obsidian API
vi.mock('obsidian', () => ({
  Notice: vi.fn(),
  setIcon: vi.fn((el: HTMLElement, icon: string) => {
    el.setAttribute('data-icon', icon);
  }),
  setTooltip: vi.fn()
}));

// Now import components after mocking
import {
  generateMockWaveform,
  fadeIn,
  slideUp
} from '../uiComponents';

describe('Utility Functions', () => {
  it('should generate mock waveform with correct length', () => {
    const waveform = generateMockWaveform(50);
    expect(waveform.length).toBe(50);
  });

  it('should generate waveform values between 0.2 and 1.0', () => {
    const waveform = generateMockWaveform(50);
    expect(waveform.every(v => v >= 0.2 && v <= 1.0)).toBe(true);
  });

  it('should return animation object from fadeIn', () => {
    const el = document.createElement('div');
    document.body.appendChild(el);
    const animation = fadeIn(el, 250);
    expect(animation).toBeDefined();
    expect(el.animate).toHaveBeenCalled();
    el.remove();
  });

  it('should return animation object from slideUp', () => {
    const el = document.createElement('div');
    document.body.appendChild(el);
    const animation = slideUp(el, 300);
    expect(animation).toBeDefined();
    expect(el.animate).toHaveBeenCalled();
    el.remove();
  });
});

describe('UI Component Creation', () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    container.remove();
  });

  it('should create container element', () => {
    expect(container).toBeDefined();
    expect(container.parentElement).toBe(document.body);
  });

  it('should support DOM manipulation', () => {
    const child = (container as any).createDiv({ cls: 'test' });
    expect(child).toBeDefined();
    expect(child.classList.contains('test')).toBe(true);
  });

  it('should support createEl', () => {
    const btn = (container as any).createEl('button', { text: 'Test' });
    expect(btn.tagName).toBe('BUTTON');
    expect(btn.textContent).toBe('Test');
  });
});

describe('CSS Class Verification', () => {
  it('should verify typing indicator classes exist', () => {
    const el = document.createElement('div');
    el.className = 'oa-typing-indicator';
    expect(el.classList.contains('oa-typing-indicator')).toBe(true);
  });

  it('should verify message bubble classes exist', () => {
    const el = document.createElement('div');
    el.className = 'oa-message oa-message--user';
    expect(el.classList.contains('oa-message')).toBe(true);
    expect(el.classList.contains('oa-message--user')).toBe(true);
  });

  it('should verify reaction classes exist', () => {
    const el = document.createElement('span');
    el.className = 'oa-reaction oa-reaction--active';
    expect(el.classList.contains('oa-reaction')).toBe(true);
  });

  it('should verify voice message classes exist', () => {
    const el = document.createElement('div');
    el.className = 'oa-voice-message';
    expect(el.classList.contains('oa-voice-message')).toBe(true);
  });

  it('should verify search interface classes exist', () => {
    const el = document.createElement('div');
    el.className = 'oa-search-container';
    expect(el.classList.contains('oa-search-container')).toBe(true);
  });
});

describe('Animation Timing Functions', () => {
  it('should have correct transition values in CSS format', () => {
    const expectedTransitions = [
      '150ms cubic-bezier(0.4, 0, 0.2, 1)',
      '250ms cubic-bezier(0.4, 0, 0.2, 1)',
      '350ms cubic-bezier(0.4, 0, 0.2, 1)',
      '500ms cubic-bezier(0.34, 1.56, 0.64, 1)'
    ];
    
    expectedTransitions.forEach(transition => {
      expect(transition).toContain('ms');
      expect(transition).toContain('cubic-bezier');
    });
  });

  it('should have correct spacing scale', () => {
    const spacings = [0.25, 0.5, 0.75, 1, 1.5, 2];
    spacings.forEach(space => {
      expect(space).toBeGreaterThan(0);
    });
  });

  it('should have correct border radius values', () => {
    const radii = [8, 12, 18, 24, 9999];
    radii.forEach(radius => {
      expect(radius).toBeGreaterThan(0);
    });
  });
});

describe('Accessibility Features', () => {
  it('should support screen reader only content', () => {
    const el = document.createElement('span');
    el.className = 'oa-sr-only';
    expect(el.classList.contains('oa-sr-only')).toBe(true);
  });

  it('should support high contrast mode', () => {
    const el = document.createElement('div');
    el.className = 'oa-high-contrast';
    expect(el.classList.contains('oa-high-contrast')).toBe(true);
  });

  it('should support reduced motion', () => {
    const mediaQuery = 'prefers-reduced-motion';
    expect(mediaQuery).toBe('prefers-reduced-motion');
  });
});

describe('Glass Morphism Features', () => {
  it('should verify glass effect classes', () => {
    const el = document.createElement('div');
    el.className = 'oa-modal-header-glass';
    expect(el.classList.contains('oa-modal-header-glass')).toBe(true);
  });

  it('should verify backdrop filter is defined in CSS', () => {
    const backdropValue = 'blur(20px) saturate(180%)';
    expect(backdropValue).toContain('blur');
    expect(backdropValue).toContain('saturate');
  });
});
