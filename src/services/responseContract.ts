/**
 * Structured Agent Response Contract
 * 
 * Enforces consistent output format for all agent interactions.
 * Ensures quality, traceability, and actionability.
 */

export interface StructuredAgentResponse {
  answer: string; // Natural language answer to user query
  evidence: Evidence; // Supporting data and sources
  confidence: ConfidenceScore; // Multi-dimensional confidence
  recommendedAction?: RecommendedAction; // Next steps for user
  metadata: ResponseMetadata; // Execution details
}

export interface Evidence {
  sources: Source[]; // Documents/notes cited
  totalMatches: number; // Total results found
  reasoning?: string; // Chain of thought
  toolsUsed: string[]; // Tools invoked during execution
}

export interface Source {
  path: string; // File path or identifier
  relevance: number; // 0-1 similarity score
  excerpt: string; // Preview text
  metadata?: Record<string, any>; // Additional context
}

export interface ConfidenceScore {
  overall: number; // 0-1 aggregate confidence
  dimensions: {
    sourceQuality: number; // Quality of retrieved sources
    reasoning: number; // Logical coherence
    completeness: number; // Answer completeness
    certainty: number; // AI certainty in answer
  };
  explanation?: string; // Why this confidence level
}

export interface RecommendedAction {
  type: 'search' | 'create' | 'update' | 'read' | 'none';
  description: string; // Human-readable action
  parameters?: Record<string, any>; // Action parameters
  priority: 'low' | 'medium' | 'high';
}

export interface ResponseMetadata {
  operationId: string;
  duration: number; // Execution time in ms
  steps: number; // ReAct steps taken
  tokensUsed?: number;
  model?: string;
  timestamp: number;
  success: boolean;
  error?: string;
}

/**
 * ResponseValidator - Validates agent responses against contract
 */
export class ResponseValidator {
  validate(response: StructuredAgentResponse): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    // Required fields
    if (!response.answer || response.answer.trim().length === 0) {
      errors.push('Answer is empty');
    }

    if (!response.evidence) {
      errors.push('Evidence is missing');
    } else {
      if (!Array.isArray(response.evidence.sources)) {
        errors.push('Evidence.sources must be an array');
      }
      if (typeof response.evidence.totalMatches !== 'number') {
        errors.push('Evidence.totalMatches must be a number');
      }
      if (!Array.isArray(response.evidence.toolsUsed)) {
        errors.push('Evidence.toolsUsed must be an array');
      }
    }

    if (!response.confidence) {
      errors.push('Confidence is missing');
    } else {
      if (
        response.confidence.overall < 0 ||
        response.confidence.overall > 1
      ) {
        errors.push('Confidence.overall must be between 0 and 1');
      }
      if (!response.confidence.dimensions) {
        errors.push('Confidence.dimensions is missing');
      }
    }

    if (!response.metadata) {
      errors.push('Metadata is missing');
    } else {
      if (!response.metadata.operationId) {
        errors.push('Metadata.operationId is required');
      }
      if (typeof response.metadata.duration !== 'number') {
        errors.push('Metadata.duration must be a number');
      }
      if (typeof response.metadata.success !== 'boolean') {
        errors.push('Metadata.success must be a boolean');
      }
    }

    // Validate sources
    if (response.evidence?.sources) {
      for (const [i, source] of response.evidence.sources.entries()) {
        if (!source.path) {
          errors.push(`Source ${i}: path is required`);
        }
        if (
          typeof source.relevance !== 'number' ||
          source.relevance < 0 ||
          source.relevance > 1
        ) {
          errors.push(`Source ${i}: relevance must be between 0 and 1`);
        }
        if (!source.excerpt) {
          errors.push(`Source ${i}: excerpt is required`);
        }
      }
    }

    // Validate recommended action if present
    if (response.recommendedAction) {
      const validTypes = ['search', 'create', 'update', 'read', 'none'];
      if (!validTypes.includes(response.recommendedAction.type)) {
        errors.push(
          `RecommendedAction.type must be one of: ${validTypes.join(', ')}`
        );
      }
      if (!response.recommendedAction.description) {
        errors.push('RecommendedAction.description is required');
      }
      const validPriorities = ['low', 'medium', 'high'];
      if (!validPriorities.includes(response.recommendedAction.priority)) {
        errors.push(
          `RecommendedAction.priority must be one of: ${validPriorities.join(', ')}`
        );
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Calculate quality score based on response characteristics
   */
  calculateQualityScore(response: StructuredAgentResponse): number {
    let score = 0;

    // Answer length (10 points)
    const answerLength = response.answer.length;
    if (answerLength > 500) score += 10;
    else if (answerLength > 200) score += 7;
    else if (answerLength > 50) score += 4;

    // Evidence quality (30 points)
    const sourceCount = response.evidence.sources.length;
    if (sourceCount >= 3) score += 15;
    else if (sourceCount >= 1) score += 10;

    const avgRelevance =
      sourceCount > 0
        ? response.evidence.sources.reduce((sum, s) => sum + s.relevance, 0) /
          sourceCount
        : 0;
    if (avgRelevance > 0.8) score += 15;
    else if (avgRelevance > 0.6) score += 10;
    else if (avgRelevance > 0.4) score += 5;

    // Confidence (30 points)
    score += response.confidence.overall * 30;

    // Reasoning (10 points)
    if (response.evidence.reasoning && response.evidence.reasoning.length > 50) {
      score += 10;
    }

    // Recommended action (10 points)
    if (response.recommendedAction) {
      score += 10;
    }

    // Metadata completeness (10 points)
    let metaScore = 0;
    if (response.metadata.tokensUsed) metaScore += 3;
    if (response.metadata.model) metaScore += 3;
    if (response.metadata.steps > 0) metaScore += 4;
    score += metaScore;

    return Math.min(score, 100);
  }
}

/**
 * ResponseBuilder - Fluent builder for creating structured responses
 */
export class ResponseBuilder {
  private response: Partial<StructuredAgentResponse> = {
    evidence: {
      sources: [],
      totalMatches: 0,
      toolsUsed: [],
    },
    confidence: {
      overall: 0,
      dimensions: {
        sourceQuality: 0,
        reasoning: 0,
        completeness: 0,
        certainty: 0,
      },
    },
    metadata: {
      operationId: '',
      duration: 0,
      steps: 0,
      timestamp: Date.now(),
      success: false,
    },
  };

  setAnswer(answer: string): this {
    this.response.answer = answer;
    return this;
  }

  addSource(source: Source): this {
    this.response.evidence!.sources.push(source);
    this.response.evidence!.totalMatches++;
    return this;
  }

  setSources(sources: Source[]): this {
    this.response.evidence!.sources = sources;
    this.response.evidence!.totalMatches = sources.length;
    return this;
  }

  setReasoning(reasoning: string): this {
    this.response.evidence!.reasoning = reasoning;
    return this;
  }

  addToolUsed(tool: string): this {
    if (!this.response.evidence!.toolsUsed.includes(tool)) {
      this.response.evidence!.toolsUsed.push(tool);
    }
    return this;
  }

  setConfidence(overall: number, dimensions?: Partial<ConfidenceScore['dimensions']>): this {
    this.response.confidence!.overall = overall;
    if (dimensions) {
      Object.assign(this.response.confidence!.dimensions, dimensions);
    }
    return this;
  }

  setConfidenceExplanation(explanation: string): this {
    this.response.confidence!.explanation = explanation;
    return this;
  }

  setRecommendedAction(action: RecommendedAction): this {
    this.response.recommendedAction = action;
    return this;
  }

  setMetadata(metadata: Partial<ResponseMetadata>): this {
    Object.assign(this.response.metadata!, metadata);
    return this;
  }

  markSuccess(): this {
    this.response.metadata!.success = true;
    return this;
  }

  markFailure(error: string): this {
    this.response.metadata!.success = false;
    this.response.metadata!.error = error;
    return this;
  }

  build(): StructuredAgentResponse {
    const validator = new ResponseValidator();
    const result = validator.validate(this.response as StructuredAgentResponse);

    if (!result.valid) {
      throw new Error(
        `Invalid response structure: ${result.errors.join('; ')}`
      );
    }

    return this.response as StructuredAgentResponse;
  }

  buildUnsafe(): StructuredAgentResponse {
    return this.response as StructuredAgentResponse;
  }
}
