import { AIService } from '../../../aiService';
import { Tool } from './tools';
import { ObsidianAgentSettings } from '../../../settings';
import { 
    parseAgentResponse, 
    validateResponse, 
    calculateMomentumScore,
    isDeadEnd
} from '../../types/agentResponse';
import { ConversationMemory } from '../../intelligence/memory/conversationMemory';
import { ConfidenceEstimator } from '../../intelligence/reasoning/confidenceEstimator';

export class AgentService {
    private aiService: AIService;
    private tools: Tool[];
    private maxSteps: number = 10;
    private settings: ObsidianAgentSettings;
    private momentumThreshold: number = 8; // Minimum score to avoid rewrite
    private conversationMemory: ConversationMemory;
    private confidenceEstimator: ConfidenceEstimator;

    constructor(aiService: AIService, tools: Tool[], settings: ObsidianAgentSettings) {
        this.aiService = aiService;
        this.tools = tools;
        this.settings = settings;
        this.conversationMemory = new ConversationMemory();
        this.confidenceEstimator = new ConfidenceEstimator();
    }

    async run(query: string): Promise<StructuredAgentResponse> {
        // Add user query to conversation memory
        this.conversationMemory.addMessage('user', query);

        // Use the configurable agent core prompt with momentum policy
        let history = this.settings.agentCorePrompt + '\n\n';
        
        // Add conversation context if available
        const sessionContext = this.conversationMemory.getContext();
        if (sessionContext) {
            history += sessionContext;
        }
        
        history += 'Available tools:\n';
        
        this.tools.forEach(t => {
            history += `- ${t.name}: ${t.description}\n`;
        });

        history += `

**IMPORTANT:** Your response MUST follow the required format with a mandatory NEXT STEP section.

Example response structure:
"""
Based on your query, here's what I found...

**Why this works:**
This approach is effective because...

---
**🎯 NEXT STEP:**
- **Action**: Create a new note titled "Project Ideas" in the Projects folder
- **Owner**: agent
- **Effort**: 5m
- **Success looks like**: New note exists with proper frontmatter and initial structure

**Alternative paths:**
1. Use an existing note - Use when you have a similar note already
2. Create a template first - Use when you'll make many similar notes

**⚠️ Watch out for:**
- Duplicate note names
- Missing folder structure

**Mitigation:**
- Check if note exists first
- Create folders if needed
"""

User's question: ${query}

`;

        let steps = 0;
        let retryCount = 0;
        const maxRetries = 2;
        const context: any = {
            toolsUsed: [],
            vaultSearchResults: 0
        };
        
        while (steps < this.maxSteps) {
            steps++;
            
            // Call AI
            const result = await this.aiService.generateCompletion({ prompt: history });
            const response = result.text;
            
            history += response + '\n';

            // Check if this looks like a final conversational answer (not using tools)
            const hasAction = response.includes('Action:') && response.includes('Action Input:');
            
            if (!hasAction) {
                // This is a direct answer - validate it has forward motion
                const parsedResponse = parseAgentResponse(response);
                const validation = validateResponse(parsedResponse);
                const momentumScore = calculateMomentumScore(parsedResponse);
                const deadEnd = isDeadEnd(response);

                // If response is invalid or lacks momentum, try to get a better one
                if (!validation.valid || momentumScore < this.momentumThreshold || deadEnd) {
                    if (retryCount < maxRetries) {
                        retryCount++;
                        let feedback = '\n\n';
                        
                        if (!validation.valid) {
                            feedback += `❌ Your response is missing required elements: ${validation.missing_fields?.join(', ')}\n`;
                            feedback += `Suggestions: ${validation.suggestions?.join('; ')}\n\n`;
                        } else if (deadEnd) {
                            feedback += `❌ Your response appears to be a dead-end (no clear path forward).\n`;
                            feedback += `Please provide a concrete next step or recommendation.\n\n`;
                        } else if (momentumScore < this.momentumThreshold) {
                            feedback += `❌ Your response lacks sufficient forward motion (score: ${momentumScore}/10).\n`;
                            feedback += `Please include a more detailed next step with clear action, effort, and expected outcome.\n\n`;
                        }
                        
                        feedback += `Remember the MOMENTUM POLICY: Every response MUST include:\n`;
                        feedback += `- A direct answer\n`;
                        feedback += `- A mandatory 🎯 NEXT STEP section with action, owner, effort, and expected outcome\n`;
                        feedback += `- Optional: alternatives, risks, and mitigation\n\n`;
                        feedback += `Please revise your response to include all required elements:\n`;
                        
                        history += feedback;
                        continue; // Loop again to get better response
                    }
                }

                // Calculate confidence score
                const toolsUsed = context.toolsUsed || [];
                const vaultSearchResults = context.vaultSearchResults || 0;
                const confidenceScore = this.confidenceEstimator.estimate(response, {
                    vaultSearchResults,
                    toolsUsed,
                    reasoningSteps: steps
                });

                // Add response to conversation memory
                this.conversationMemory.addMessage('agent', response, {
                    tools_used: toolsUsed,
                    confidence: confidenceScore.overall,
                    intent: 'answer'
                });

                // Build final response with confidence info
                let finalResponse = response.trim();

                // Add confidence warning if low
                if (confidenceScore.level === 'medium' || confidenceScore.level === 'low') {
                    finalResponse += '\n' + this.confidenceEstimator.formatConfidence(confidenceScore);
                }

                // Valid response with good momentum - return it
                return finalResponse;
            }

            // Parse tool use
            const actionMatch = response.match(/Action:\s*(.+?)$/m);
            const inputMatch = response.match(/Action Input:\s*(.+?)$/m);

            if (actionMatch && inputMatch) {
                const action = actionMatch[1].trim();
                const input = inputMatch[1].trim();
                
                const tool = this.tools.find(t => t.name === action);
                
                if (tool) {
                    // Track tool usage
                    context.toolsUsed.push(action);
                    
                    const observation = await tool.execute(input);
                    history += `Observation: ${observation}\n\n`;
                    
                    // Track if this was a search
                    if (action.toLowerCase().includes('search')) {
                        // Rough heuristic: count lines or result markers
                        const resultCount = (observation.match(/\n/g) || []).length;
                        context.vaultSearchResults = Math.max(context.vaultSearchResults, resultCount);
                    }
                    
                    // If observation is empty or indicates no results, guide the AI to be helpful
                    if (!observation || observation.includes('No results') || observation.includes('not found')) {
                        history += `(Remember: When search returns no results, offer to help create new content or suggest related topics instead of just reporting the empty result.)\n\n`;
                    }
                } else {
                    history += `Observation: Error - tool "${action}" not found. Available tools: ${this.tools.map(t => t.name).join(', ')}\n\n`;
                }
            } else {
                // Malformed response - return what we got
                return response.trim();
            }
        }

        return "I apologize, but I wasn't able to complete that request within the expected time. Could you try rephrasing your question?";
    }

    /**
     * Clear conversation memory (new session)
     */
    clearMemory(): void {
        this.conversationMemory.clear();
    }

    /**
     * Get conversation summary
     */
    getConversationSummary(): string {
        return this.conversationMemory.getSummary();
    }
}
