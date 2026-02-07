/**
 * Response Contract - Ensures every agent response includes forward motion
 */

export interface NextStep {
    action: string;
    owner: 'user' | 'agent';
    effort: '5m' | '30m' | 'half-day' | '1-day' | '2-days+';
    expected_outcome: string;
    type?: 'do_now' | 'choose_path' | 'unblock';
}

export interface Alternative {
    option: string;
    when_to_use: string;
    trade_offs?: string;
}

export interface AgentResponse {
    answer: string;
    reasoning_summary: string;
    next_step: NextStep;
    alternatives?: Alternative[];
    risks?: string[];
    mitigation?: string[];
}

/**
 * Response quality metrics
 */
export interface ResponseMetrics {
    factuality: number;    // 0-10
    relevance: number;     // 0-10
    actionability: number; // 0-10
    momentum: number;      // 0-10
}

/**
 * Validation result
 */
export interface ValidationResult {
    valid: boolean;
    reason?: string;
    missing_fields?: string[];
    suggestions?: string[];
}

/**
 * Parse agent output and extract structured response
 * Supports both legacy markdown and new YAML block format
 */
export function parseAgentResponse(rawOutput: string): Partial<AgentResponse> {
    const response: Partial<AgentResponse> = {
        answer: '',
        reasoning_summary: '',
        alternatives: [],
        risks: [],
        mitigation: []
    };

    // Try to extract from YAML block first
    const yamlMatch = rawOutput.match(/```yaml\n([\s\S]*?)```/);
    if (yamlMatch) {
        const yamlContent = yamlMatch[1];
        
        // Basic key-value extraction for simple fields
        const answerMatch = yamlContent.match(/answer:\s*(.+)/);
        if (answerMatch) response.answer = answerMatch[1].trim();

        const reasoningMatch = yamlContent.match(/reasoning_summary:\s*(.+)/);
        if (reasoningMatch) response.reasoning_summary = reasoningMatch[1].trim();

        // Extract next_step block
        const nextStepBlock = yamlContent.match(/next_step:\s*\n((?:\s+.*\n?)*)/);
        if (nextStepBlock) {
            const block = nextStepBlock[1];
            const action = block.match(/\s+action:\s*(.+)/)?.[1];
            const owner = block.match(/\s+owner:\s*(user|agent)/)?.[1];
            const effort = block.match(/\s+effort:\s*(\d+m|half-day|1-day|2-days\+)/)?.[1];
            const outcome = block.match(/\s+expected_outcome:\s*(.+)/)?.[1];
            const type = block.match(/\s+type:\s*(do_now|choose_path|unblock)/)?.[1];

            if (action) {
                response.next_step = {
                    action: action.trim(),
                    owner: (owner as 'user' | 'agent') || 'user',
                    effort: (effort as any) || '30m',
                    expected_outcome: outcome?.trim() || 'Task completed successfully',
                    type: type as any
                };
            }
        }

        // If YAML parsing failed to get answer, use the whole text outside YAML as answer
        if (!response.answer) {
            response.answer = rawOutput.replace(/```yaml[\s\S]*?```/, '').trim();
        }
    } else {
        // Fallback to legacy markdown parsing
        response.answer = rawOutput;
        
        // Extract next step if present in legacy format
        const nextStepMatch = rawOutput.match(/(?:NEXT STEP|Next Step|🎯 NEXT STEP):\s*\n([\s\S]*?)(?=\n\n|$)/i);
        if (nextStepMatch) {
            const nextStepText = nextStepMatch[1];
            const actionMatch = nextStepText.match(/[-*]\s*(?:Action|action):\s*(.+)/i);
            const ownerMatch = nextStepText.match(/[-*]\s*(?:Owner|owner):\s*(user|agent)/i);
            const effortMatch = nextStepText.match(/[-*]\s*(?:Effort|effort):\s*(\d+m|half-day|1-day|2-days\+)/i);
            const outcomeMatch = nextStepText.match(/[-*]\s*(?:Success looks like|Expected outcome|expected_outcome):\s*(.+)/i);

            if (actionMatch) {
                response.next_step = {
                    action: actionMatch[1].trim(),
                    owner: (ownerMatch?.[1] as 'user' | 'agent') || 'user',
                    effort: (effortMatch?.[1] as any) || '30m',
                    expected_outcome: outcomeMatch?.[1].trim() || 'Task completed successfully'
                };
            }
        }
    }

    return response;
}

/**
 * Validate agent response has required forward motion
 */
export function validateResponse(response: Partial<AgentResponse>): ValidationResult {
    const missing: string[] = [];

    if (!response.answer && !response.next_step) {
        missing.push('answer');
    }

    if (!response.next_step) {
        return {
            valid: false,
            reason: 'Missing mandatory next_step field',
            missing_fields: ['next_step'],
            suggestions: [
                'Add a concrete action the user or agent should take',
                'Specify who owns the next action (user or agent)',
                'Estimate effort required',
                'Describe what success looks like',
                'Specify the continuation type (do_now, choose_path, unblock)'
            ]
        };
    }

    if (!response.next_step.action || response.next_step.action.length < 5) {
        missing.push('next_step.action');
    }

    if (!response.next_step.expected_outcome) {
        missing.push('next_step.expected_outcome');
    }

    if (missing.length > 0) {
        return {
            valid: false,
            reason: 'Incomplete next_step information',
            missing_fields: missing,
            suggestions: ['Provide more detail for the next step']
        };
    }

    return { valid: true };
}

/**
 * Calculate momentum score for a response
 */
export function calculateMomentumScore(response: Partial<AgentResponse>): number {
    let score = 0;

    // Has next step? (+4 points)
    if (response.next_step?.action) {
        score += 4;
    }

    // Action is specific? (+2 points)
    if (response.next_step?.action && response.next_step.action.length > 20) {
        score += 2;
    }

    // Has expected outcome? (+2 points)
    if (response.next_step?.expected_outcome) {
        score += 2;
    }

    // Has alternatives? (+1 point)
    if (response.alternatives && response.alternatives.length > 0) {
        score += 1;
    }

    // Has risk awareness? (+1 point)
    if (response.risks && response.risks.length > 0) {
        score += 1;
    }

    return score;
}

/**
 * Format response for display
 */
export function formatAgentResponse(response: Partial<AgentResponse>): string {
    let output = '';

    // Main answer
    if (response.answer) {
        output += response.answer + '\n\n';
    }

    // Reasoning (if separate from answer)
    if (response.reasoning_summary && response.reasoning_summary !== response.answer) {
        output += `**Why this works:**\n${response.reasoning_summary}\n\n`;
    }

    // Next step (mandatory)
    if (response.next_step) {
        output += '---\n';
        output += '**🎯 NEXT STEP:**\n';
        output += `- **Action**: ${response.next_step.action}\n`;
        output += `- **Owner**: ${response.next_step.owner}\n`;
        output += `- **Effort**: ${response.next_step.effort}\n`;
        output += `- **Success looks like**: ${response.next_step.expected_outcome}\n`;
        if (response.next_step.type) {
            output += `- **Type**: ${response.next_step.type}\n`;
        }
        output += '\n';
    }

    // Alternatives
    if (response.alternatives && response.alternatives.length > 0) {
        output += '**Alternative paths:**\n';
        response.alternatives.forEach((alt, i) => {
            output += `${i + 1}. ${alt.option} - Use when ${alt.when_to_use}\n`;
            if (alt.trade_offs) {
                output += `   *Trade-offs: ${alt.trade_offs}*\n`;
            }
        });
        output += '\n';
    }

    // Risks
    if (response.risks && response.risks.length > 0) {
        output += '**⚠️ Watch out for:**\n';
        response.risks.forEach(risk => {
            output += `- ${risk}\n`;
        });
        output += '\n';
    }

    // Mitigation
    if (response.mitigation && response.mitigation.length > 0) {
        output += '**Mitigation:**\n';
        response.mitigation.forEach(m => {
            output += `- ${m}\n`;
        });
        output += '\n';
    }

    return output.trim();
}

/**
 * Dead-end patterns that indicate lack of forward motion
 */
export const DEAD_END_PATTERNS = [
    /it depends(?!\s+on\s+.+\.\s+(?:if|when|option))/i,
    /you could(?!\s+(?:try|do|start).*(?:\.|:)\s*(?:\d+\.|-))/i,
    /(?:let me know|tell me)\s+(?:if|what|how).*[?]$/i,
    /(?:there are many|several|various)\s+(?:ways|options|approaches)(?!\s*:\s*\d+\.)/i
];

/**
 * Check if response is a dead-end (lacks forward motion)
 */
export function isDeadEnd(output: string): boolean {
    // Check against dead-end patterns
    for (const pattern of DEAD_END_PATTERNS) {
        if (pattern.test(output)) {
            return true;
        }
    }

    // Check if ends with question without suggestion
    const endsWithQuestion = /\?\s*$/.test(output.trim());
    const hasSuggestion = /(?:i recommend|i suggest|next step|you should|start by)/i.test(output);

    if (endsWithQuestion && !hasSuggestion) {
        return true;
    }

    return false;
}
