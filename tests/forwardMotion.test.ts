import { describe, it, expect, beforeEach } from 'vitest';
import { 
    parseAgentResponse, 
    validateResponse, 
    calculateMomentumScore, 
    isDeadEnd 
} from '../src/types/agentResponse';

describe('Forward Motion Logic', () => {
    describe('YAML Parser', () => {
        it('should correctly parse a valid YAML response block', () => {
            const raw = `Based on my analysis, you should organize your notes by year.
\`\`\`yaml
answer: Organize notes by year.
reasoning_summary: chronological organization is intuitive for journals.
next_step:
  action: Move 2025 notes to a new folder
  owner: agent
  effort: 5m
  expected_outcome: Folder "2025" contains all last year's notes
  type: do_now
alternatives:
  - option: Organize by tag
    when_to_use: if you prefer topic-based retrieval
risks:
  - Accidentally moving non-journal notes
mitigation:
  - Check for #journal tag before moving
\`\`\``;
            
            const parsed = parseAgentResponse(raw);
            expect(parsed.answer).toBe('Organize notes by year.');
            expect(parsed.next_step?.action).toBe('Move 2025 notes to a new folder');
            expect(parsed.next_step?.type).toBe('do_now');
            expect(parsed.reasoning_summary).toContain('chronological');
        });

        it('should fallback to markdown parsing if YAML is missing', () => {
            const raw = `I recommend doing X.
---
🎯 NEXT STEP:
- Action: Run test script
- Owner: user
- Effort: 30m
- Success looks like: tests pass`;

            const parsed = parseAgentResponse(raw);
            expect(parsed.next_step?.action).toBe('Run test script');
            expect(parsed.next_step?.effort).toBe('30m');
        });
    });

    describe('Validation & Momentum', () => {
        it('should validate a complete next step', () => {
            const response = {
                answer: 'Valid answer',
                next_step: {
                    action: 'Complete task',
                    owner: 'agent' as const,
                    effort: '5m' as const,
                    expected_outcome: 'Done',
                    type: 'do_now' as const
                }
            };
            const result = validateResponse(response);
            expect(result.valid).toBe(true);
        });

        it('should reject incomplete next steps', () => {
            const response = {
                answer: 'Valid answer',
                next_step: {
                    action: 'Too short', // < 5 chars
                    owner: 'user' as const,
                    effort: '30m' as const,
                    expected_outcome: '',
                }
            };
            const result = validateResponse(response as any);
            expect(result.valid).toBe(false);
            expect(result.missing_fields).toContain('next_step.expected_outcome');
        });

        it('should calculate high momentum score for specific actions', () => {
            const response = {
                next_step: {
                    action: 'Refactor the entire AIService.ts file to use the new provider pattern',
                    expected_outcome: 'Code is cleaner'
                },
                alternatives: [{ option: 'Keep it', when_to_use: 'never' }]
            };
            const score = calculateMomentumScore(response as any);
            expect(score).toBeGreaterThanOrEqual(7); // 4 (has action) + 2 (long/specific) + 1 (alts)
        });
    });

    describe('Dead-end Detection', () => {
        it('should detect "it depends" without follow-up', () => {
            expect(isDeadEnd("It depends on what you want.")).toBe(true);
        });

        it('should not mark as dead-end if a suggestion follows', () => {
            expect(isDeadEnd("It depends on your goals. I suggest starting with a search.")).toBe(false);
        });

        it('should detect trailing questions without suggestions', () => {
            expect(isDeadEnd("I can help with that. What do you think?")).toBe(true);
        });
    });
});
