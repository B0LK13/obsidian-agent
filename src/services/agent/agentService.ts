import { AIService } from '../../../aiService';
import { Tool } from './tools';

export class AgentService {
    private aiService: AIService;
    private tools: Tool[];
    private maxSteps: number = 10;

    constructor(aiService: AIService, tools: Tool[]) {
        this.aiService = aiService;
        this.tools = tools;
    }

    async run(query: string): Promise<string> {
        let history = `You are an intelligent agent with access to the following tools:

`;
        
        this.tools.forEach(t => {
            history += `${t.name}: ${t.description}
`;
        });

        history += `
Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [${this.tools.map(t => t.name).join(', ')}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: ${query}
`;

        let steps = 0;
        
        while (steps < this.maxSteps) {
            steps++;
            
            // Call AI
            const result = await this.aiService.generateCompletion({ prompt: history }); // We're treating history as prompt
            const response = result.text;
            
            history += response + '\n';

            // Check for Final Answer
            if (response.includes('Final Answer:')) {
                const finalAnswer = response.split('Final Answer:')[1].trim();
                return finalAnswer;
            }

            // Check for Action
            const actionMatch = response.match(/Action: (.*)/);
            const inputMatch = response.match(/Action Input: (.*)/);

            if (actionMatch && inputMatch) {
                const action = actionMatch[1].trim();
                const input = inputMatch[1].trim();
                
                const tool = this.tools.find(t => t.name === action);
                
                if (tool) {
                    const observation = await tool.execute(input);
                    history += `Observation: ${observation}
`;
                } else {
                    history += `Observation: Error: Tool "${action}" not found.
`;
                }
            } else {
                // If AI didn't follow format, force it or just break
                // For robustness, let's treat it as a final answer if it looks like one, or ask it to continue
                if (!response.includes('Action:')) {
                     return response; // Assume it just answered directly
                }
            }
        }

        return "Error: Agent reached maximum steps without a final answer.";
    }
}
