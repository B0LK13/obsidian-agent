import { describe, it, expect, beforeEach } from 'vitest';
import {
  ResponseValidator,
  ResponseBuilder,
  StructuredAgentResponse,
} from '../src/services/responseContract';

describe('ResponseValidator', () => {
  let validator: ResponseValidator;

  beforeEach(() => {
    validator = new ResponseValidator();
  });

  it('should validate a complete response', () => {
    const response: StructuredAgentResponse = {
      answer: 'This is a valid answer',
      evidence: {
        sources: [
          {
            path: 'note.md',
            relevance: 0.85,
            excerpt: 'Relevant excerpt',
          },
        ],
        totalMatches: 1,
        toolsUsed: ['search_vault'],
      },
      confidence: {
        overall: 0.8,
        dimensions: {
          sourceQuality: 0.9,
          reasoning: 0.8,
          completeness: 0.7,
          certainty: 0.8,
        },
      },
      metadata: {
        operationId: 'op-123',
        duration: 1500,
        steps: 3,
        timestamp: Date.now(),
        success: true,
      },
    };

    const result = validator.validate(response);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should reject response with missing answer', () => {
    const response: any = {
      answer: '',
      evidence: { sources: [], totalMatches: 0, toolsUsed: [] },
      confidence: { overall: 0.5, dimensions: {} },
      metadata: { operationId: 'op-123', duration: 100, success: true },
    };

    const result = validator.validate(response);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Answer is empty');
  });

  it('should reject response with invalid confidence', () => {
    const response: any = {
      answer: 'Test',
      evidence: { sources: [], totalMatches: 0, toolsUsed: [] },
      confidence: { overall: 1.5, dimensions: {} }, // Invalid: > 1
      metadata: { operationId: 'op-123', duration: 100, success: true },
    };

    const result = validator.validate(response);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes('between 0 and 1'))).toBe(true);
  });

  it('should reject sources with invalid relevance', () => {
    const response: any = {
      answer: 'Test',
      evidence: {
        sources: [
          { path: 'note.md', relevance: 1.2, excerpt: 'test' }, // Invalid
        ],
        totalMatches: 1,
        toolsUsed: [],
      },
      confidence: { overall: 0.5, dimensions: {} },
      metadata: { operationId: 'op-123', duration: 100, success: true },
    };

    const result = validator.validate(response);
    expect(result.valid).toBe(false);
  });

  it('should calculate quality score', () => {
    const response: StructuredAgentResponse = {
      answer: 'A'.repeat(600), // Long answer
      evidence: {
        sources: [
          { path: 'a.md', relevance: 0.9, excerpt: 'High relevance' },
          { path: 'b.md', relevance: 0.85, excerpt: 'Also high' },
          { path: 'c.md', relevance: 0.8, excerpt: 'Good' },
        ],
        totalMatches: 3,
        toolsUsed: ['search_vault', 'read_note'],
        reasoning: 'Detailed reasoning with more than fifty characters here.',
      },
      confidence: {
        overall: 0.9,
        dimensions: {
          sourceQuality: 0.9,
          reasoning: 0.85,
          completeness: 0.88,
          certainty: 0.92,
        },
      },
      recommendedAction: {
        type: 'read',
        description: 'Read the full notes for more details',
        priority: 'medium',
      },
      metadata: {
        operationId: 'op-123',
        duration: 2000,
        steps: 5,
        tokensUsed: 1500,
        model: 'gpt-4',
        timestamp: Date.now(),
        success: true,
      },
    };

    const score = validator.calculateQualityScore(response);
    expect(score).toBeGreaterThan(70); // High-quality response
    expect(score).toBeLessThanOrEqual(100);
  });
});

describe('ResponseBuilder', () => {
  it('should build a valid response', () => {
    const builder = new ResponseBuilder();

    const response = builder
      .setAnswer('This is the answer')
      .addSource({ path: 'note.md', relevance: 0.9, excerpt: 'Excerpt' })
      .setConfidence(0.85, { sourceQuality: 0.9, reasoning: 0.8 })
      .setMetadata({ operationId: 'op-456', duration: 1000, steps: 2 })
      .markSuccess()
      .build();

    expect(response.answer).toBe('This is the answer');
    expect(response.evidence.sources).toHaveLength(1);
    expect(response.confidence.overall).toBe(0.85);
    expect(response.metadata.success).toBe(true);
  });

  it('should throw error if build() called with incomplete data', () => {
    const builder = new ResponseBuilder();
    builder.setAnswer('Only answer set');

    expect(() => builder.build()).toThrow();
  });

  it('should allow unsafe build', () => {
    const builder = new ResponseBuilder();
    builder.setAnswer('Incomplete');

    const response = builder.buildUnsafe();
    expect(response.answer).toBe('Incomplete');
    // No validation, may be incomplete
  });

  it('should accumulate tools used', () => {
    const builder = new ResponseBuilder();

    builder
      .addToolUsed('search_vault')
      .addToolUsed('read_note')
      .addToolUsed('search_vault'); // Duplicate

    const response = builder.buildUnsafe();
    expect(response.evidence.toolsUsed).toHaveLength(2); // No duplicates
  });

  it('should set recommended action', () => {
    const builder = new ResponseBuilder();

    builder
      .setAnswer('Answer')
      .setRecommendedAction({
        type: 'create',
        description: 'Create a new note',
        priority: 'high',
      })
      .setConfidence(0.5)
      .setMetadata({ operationId: 'op-789', duration: 500, steps: 1 })
      .markSuccess();

    const response = builder.build();
    expect(response.recommendedAction).toBeTruthy();
    expect(response.recommendedAction!.type).toBe('create');
    expect(response.recommendedAction!.priority).toBe('high');
  });

  it('should handle failure marking', () => {
    const builder = new ResponseBuilder();

    builder
      .setAnswer('Failed attempt')
      .setConfidence(0.0)
      .setMetadata({ operationId: 'op-fail', duration: 100, steps: 0 })
      .markFailure('Network timeout');

    const response = builder.buildUnsafe();
    expect(response.metadata.success).toBe(false);
    expect(response.metadata.error).toBe('Network timeout');
  });
});
