import { AIService } from '../../../aiService';
import { Tool } from './tools';
import { ObsidianAgentSettings } from '../../../settings';
import { 
    parseAgentResponse, 
    validateResponse, 
    calculateMomentumScore,
    isDeadEnd,
    formatAgentResponse,
    AgentResponse
} from '../../types/agentResponse';
import { ConversationMemory } from '../../intelligence/memory/conversationMemory';
import { ConfidenceEstimator, ConfidenceScore } from '../../intelligence/reasoning/confidenceEstimator';
import { MemoryService } from '../memoryService';

export class AgentService {
    private aiService: AIService;
    private tools: Tool[];
    private maxSteps: number = 10;
    private settings: ObsidianAgentSettings;
    private momentumThreshold: number = 8;
    private conversationMemory: ConversationMemory;
    private memoryService: MemoryService;
    private confidenceEstimator: ConfidenceEstimator;

    constructor(aiService: AIService, tools: Tool[], settings: ObsidianAgentSettings, memoryService: MemoryService) {
        this.aiService = aiService;
        this.tools = tools;
        this.settings = settings;
        this.memoryService = memoryService;
        this.conversationMemory = new ConversationMemory();
        this.confidenceEstimator = new ConfidenceEstimator();
    }

    async run(query: string): Promise<string> {
        this.conversationMemory.addMessage('user', query);
        const memoryLayers = await this.memoryService.getContextualMemory(query);

        let instructions = this.settings.agentCorePrompt + '\n\n';
        instructions += this.getEnforcementInstructions();

        let history = instructions + '\n';
        history += this.formatMemoryContext(memoryLayers);
        
        const sessionContext = this.conversationMemory.getContext();
        if (sessionContext) history += "Recent Conversation:\n" + sessionContext + "\n";

        history += 'Available tools:\n';
        this.tools.forEach(t => {
          history += `- ${t.name}: ${t.description}\n`;
        });
        history += `\nUser's question: ${query}\n`;

        let steps = 0;
        let retryCount = 0;
        const maxRetries = 2;
        const executionContext: any = { toolsUsed: [], vaultSearchResults: 0 };

        while (steps < this.maxSteps) {
            steps++;
            const result = await this.aiService.generateCompletion({ prompt: history });
            const response = result.text;

            const actionMatch = response.match(/Action:\s*(.+?)$/m);
            const inputMatch = response.match(/Action Input:\s*(.+?)$/m);

            if (actionMatch && inputMatch) {
                history += response + '\n';
                const action = actionMatch[1].trim();
                const tool = this.tools.find(t => t.name === action);

                if (tool) {
                    executionContext.toolsUsed.push(action);
                    try {
                        const observation = await tool.execute(inputMatch[1].trim());
                        history += `Observation: ${observation}\n\n`;
                        if (action.toLowerCase().includes('search')) {
                            executionContext.vaultSearchResults = Math.max(executionContext.vaultSearchResults, (observation.match(/\n/g) || []).length);
                        }
                    } catch (error: any) {
                        history += `Observation: Error executing tool - ${error.message}\n\n`;
                    }
                } else {
                    history += `Observation: Error - tool "${action}" not found.\n\n`;
                }
                continue;
            }

            // Final answer logic with self-evaluation
            const parsed = parseAgentResponse(response);
            const evaluation = this.evaluateResponse(parsed, response, executionContext, steps);

            if (!evaluation.valid || evaluation.momentumScore < this.momentumThreshold) {
                if (retryCount < maxRetries) {
                    retryCount++;
                    history += response + `\n\n**SELF-EVALUATION FEEDBACK (Retry ${retryCount}/${maxRetries}):**\n` + evaluation.feedback;
                    continue;
                } else {
                    // Fallback Ladder trigger
                    return this.applyFallbackLadder(parsed, evaluation.confidence);
                }
            }

            // Success - add to memory and return
            this.conversationMemory.addMessage('agent', response, {
                tools_used: executionContext.toolsUsed,
                confidence: evaluation.confidence.overall
            });

            let finalOutput = formatAgentResponse(parsed);
            if (evaluation.confidence.level !== 'high') {
                finalOutput += '\n\n' + this.confidenceEstimator.formatConfidence(evaluation.confidence);
            }
            return finalOutput;
        }

        return "I apologize, but I couldn't reach a high-momentum conclusion. Recommended next move: break your request into smaller parts.";
    }

    private getEnforcementInstructions(): string {
        return `**MOMENTUM POLICY - STRICT ENFORCEMENT:**
1. Every response MUST include a concrete NEXT STEP.
2. Response is INVALID if no actionable continuation exists.
3. You must use exactly ONE of these 3 continuation types:
   - **do_now**: A single concrete action to perform immediately.
   - **choose_path**: 2-3 clear options with trade-offs.
   - **unblock**: Specific info needed if you are stuck.

**RESPONSE CONTRACT:**
Your output must include a YAML block at the end:
\`\`\`yaml
answer: <direct response>
reasoning_summary: <rationale>
next_step:
  action: <single best action>
  owner: <user|agent>
  effort: <5m|30m|half-day|1-day|2-days+>
  expected_outcome: <success criteria>
  type: <do_now|choose_path|unblock>
alternatives:
  - option: <path A>
    when_to_use: <condition>
risks:
  - <main risk>
mitigation:
  - <how to reduce risk>
\`\`\`
Maintain 70/30 ratio: 70% answer, 30% action.`;
    }

    private formatMemoryContext(layers: any): string {
        let ctx = "";
        if (layers.user.length > 0) ctx += `[User Preferences]\n${layers.user.join('\n')}\n\n`;
        if (layers.session.length > 0) ctx += `[Task Context]\n${layers.session.join('\n')}\n\n`;
        if (layers.longTerm.length > 0) ctx += `[Relevant SOPs/Knowledge]\n${layers.longTerm.join('\n')}\n\n`;
        return ctx;
    }

    private evaluateResponse(parsed: Partial<AgentResponse>, raw: string, context: any, steps: number): {
        valid: boolean;
        momentumScore: number;
        confidence: ConfidenceScore;
        feedback: string;
    } {
        const validation = validateResponse(parsed);
        const momentum = calculateMomentumScore(parsed);
        const deadEnd = isDeadEnd(raw);
        const confidence = this.confidenceEstimator.estimate(raw, {
            vaultSearchResults: context.vaultSearchResults,
            toolsUsed: context.toolsUsed,
            reasoningSteps: steps
        });

        let feedback = "";
        if (!validation.valid) feedback += `- Missing fields: ${validation.missing_fields?.join(', ')}\n`;
        if (deadEnd) feedback += `- Avoid dead-end phrasing. Propose a concrete action.\n`;
        if (momentum < this.momentumThreshold) feedback += `- Low momentum (${momentum}/10). Make the next step more specific and ambitious.\n`;

        return {
            valid: validation.valid && !deadEnd,
            momentumScore: momentum,
            confidence,
            feedback
        };
    }

    private applyFallbackLadder(parsed: Partial<AgentResponse>, confidence: ConfidenceScore): string {
        let output = parsed.answer || "I'm having trouble finding a clear path forward.";
        output += "\n\n---\n**🎯 FALLBACK PLAN:**\n";
        
        if (confidence.level === 'low') {
            output += "- **Minimal Viable Action**: I will run a diagnostic check on the current file path.\n";
            output += "- **Clarification**: I'm assuming you want to organize based on content similarity. Is that correct?\n";
            output += "- **Next Step (unblock)**: Please confirm the target folder name or provide more context on the desired structure.\n";
        } else {
            output += "- **Option A**: Proceed with current assumptions but use a temporary backup folder.\n";
            output += "- **Option B**: List all relevant tags first to manually select the best one.\n";
            output += "- **Next Step (choose_path)**: Select Option A to move fast, or Option B for more control.\n";
        }
        
        return output;
    }

    clearMemory(): void {
        this.conversationMemory.clear();
    }

    getConversationSummary(): string {
        return this.conversationMemory.getSummary();
    }
}
