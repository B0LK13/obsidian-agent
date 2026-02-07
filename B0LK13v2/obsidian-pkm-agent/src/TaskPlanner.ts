import { VaultManager } from './VaultManager';
import { MemoryManager } from './MemoryManager';
import { KnowledgeGraph } from './KnowledgeGraph';

/**
 * Task status enum
 */
type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked';

/**
 * A single task/step in a plan
 */
interface Task {
    id: string;
    description: string;
    type: 'action' | 'query' | 'decision' | 'verification';
    status: TaskStatus;
    tool?: string;
    toolArgs?: Record<string, any>;
    dependencies: string[];
    result?: string;
    error?: string;
    createdAt: number;
    completedAt?: number;
    retryCount: number;
    maxRetries: number;
}

/**
 * A plan containing multiple tasks
 */
interface Plan {
    id: string;
    goal: string;
    tasks: Task[];
    status: 'planning' | 'executing' | 'completed' | 'failed' | 'paused';
    createdAt: number;
    completedAt?: number;
    context: Record<string, any>;
}

/**
 * Goal analysis result
 */
interface GoalAnalysis {
    goal: string;
    complexity: 'simple' | 'moderate' | 'complex';
    requiredTools: string[];
    suggestedSteps: string[];
    potentialRisks: string[];
    estimatedSteps: number;
}

/**
 * TaskPlanner - Autonomous multi-step task execution with goal decomposition
 * Enables the agent to break down complex requests and execute them autonomously.
 */
export class TaskPlanner {
    private vaultManager: VaultManager;
    private memoryManager: MemoryManager;
    private knowledgeGraph: KnowledgeGraph;
    private activePlans: Map<string, Plan> = new Map();
    private completedPlans: Plan[] = [];
    private maxConcurrentTasks: number = 1;
    private maxRetries: number = 3;

    constructor(
        vaultManager: VaultManager,
        memoryManager: MemoryManager,
        knowledgeGraph: KnowledgeGraph
    ) {
        this.vaultManager = vaultManager;
        this.memoryManager = memoryManager;
        this.knowledgeGraph = knowledgeGraph;
    }

    // ============================================
    // GOAL ANALYSIS
    // ============================================

    /**
     * Analyzes a goal and provides insights for planning.
     */
    analyzeGoal(goal: string): GoalAnalysis {
        const goalLower = goal.toLowerCase();
        
        // Determine complexity
        let complexity: 'simple' | 'moderate' | 'complex' = 'simple';
        const complexIndicators = ['reorganize', 'refactor', 'migrate', 'comprehensive', 'all', 'every', 'batch'];
        const moderateIndicators = ['create and', 'update multiple', 'link', 'summarize', 'analyze'];
        
        if (complexIndicators.some(i => goalLower.includes(i))) {
            complexity = 'complex';
        } else if (moderateIndicators.some(i => goalLower.includes(i))) {
            complexity = 'moderate';
        }

        // Identify required tools
        const requiredTools: string[] = [];
        const toolPatterns: Record<string, string[]> = {
            'create_note': ['create', 'new note', 'write', 'add note'],
            'read_note': ['read', 'show', 'display', 'get content', 'what does'],
            'update_note': ['update', 'append', 'add to', 'modify'],
            'delete_note': ['delete', 'remove', 'trash'],
            'search_vault': ['search', 'find', 'look for', 'where is'],
            'search_by_tag': ['tagged with', 'with tag', 'tagged'],
            'add_tags': ['tag', 'add tag', 'label'],
            'create_link': ['link', 'connect', 'relate'],
            'get_daily_note': ['daily note', 'today', 'journal'],
            'create_zettel': ['zettel', 'atomic note', 'permanent note'],
            'create_moc': ['moc', 'map of content', 'index'],
            'move_note': ['move', 'relocate', 'organize into'],
            'rename_note': ['rename', 'change name'],
            'batch_operation': ['batch', 'bulk', 'multiple', 'all notes'],
            'analyze_connections': ['analyze', 'connections', 'related'],
            'get_vault_stats': ['statistics', 'stats', 'overview', 'how many']
        };

        for (const [tool, patterns] of Object.entries(toolPatterns)) {
            if (patterns.some(p => goalLower.includes(p))) {
                requiredTools.push(tool);
            }
        }

        // Generate suggested steps
        const suggestedSteps = this.generateSuggestedSteps(goalLower, requiredTools);

        // Identify potential risks
        const potentialRisks: string[] = [];
        if (goalLower.includes('delete') || goalLower.includes('remove')) {
            potentialRisks.push('Data loss - ensure backups exist');
        }
        if (goalLower.includes('replace') || goalLower.includes('overwrite')) {
            potentialRisks.push('Content may be overwritten - verify before proceeding');
        }
        if (goalLower.includes('all') || goalLower.includes('every')) {
            potentialRisks.push('Batch operation - may affect many files');
        }

        return {
            goal,
            complexity,
            requiredTools,
            suggestedSteps,
            potentialRisks,
            estimatedSteps: suggestedSteps.length
        };
    }

    /**
     * Generates suggested steps based on the goal.
     */
    private generateSuggestedSteps(goal: string, tools: string[]): string[] {
        const steps: string[] = [];

        // Always start with understanding
        if (tools.includes('search_vault') || tools.includes('read_note')) {
            steps.push('Gather information and understand current state');
        }

        // Creation steps
        if (tools.includes('create_note') || tools.includes('create_zettel')) {
            if (goal.includes('template')) {
                steps.push('Identify appropriate template');
            }
            steps.push('Prepare content');
            steps.push('Create the note in appropriate location');
        }

        // Modification steps
        if (tools.includes('update_note')) {
            steps.push('Read current note content');
            steps.push('Prepare updates');
            steps.push('Apply updates');
        }

        // Organization steps
        if (tools.includes('add_tags') || tools.includes('move_note')) {
            steps.push('Identify target notes');
            steps.push('Apply organizational changes');
        }

        // Linking steps
        if (tools.includes('create_link') || tools.includes('analyze_connections')) {
            steps.push('Analyze note relationships');
            steps.push('Create appropriate links');
        }

        // Verification step
        steps.push('Verify changes were applied correctly');

        return steps;
    }

    // ============================================
    // PLAN CREATION
    // ============================================

    /**
     * Creates a plan from a high-level goal.
     */
    createPlan(goal: string, context?: Record<string, any>): Plan {
        const analysis = this.analyzeGoal(goal);
        const planId = this.generateId();

        const tasks = this.decomposeTasks(goal, analysis);

        const plan: Plan = {
            id: planId,
            goal,
            tasks,
            status: 'planning',
            createdAt: Date.now(),
            context: context || {}
        };

        this.activePlans.set(planId, plan);

        // Remember this plan
        this.memoryManager.remember(
            `Created plan for: ${goal}`,
            'task',
            { tags: ['plan', 'autonomous'], importance: 0.7 }
        );

        return plan;
    }

    /**
     * Decomposes a goal into individual tasks.
     */
    private decomposeTasks(goal: string, analysis: GoalAnalysis): Task[] {
        const tasks: Task[] = [];
        const goalLower = goal.toLowerCase();

        // Simple single-action goals
        if (analysis.complexity === 'simple' && analysis.requiredTools.length === 1) {
            tasks.push(this.createTask(
                `Execute: ${goal}`,
                'action',
                analysis.requiredTools[0]
            ));
            tasks.push(this.createTask(
                'Verify completion',
                'verification',
                undefined,
                [tasks[0].id]
            ));
            return tasks;
        }

        // Multi-step goals
        let prevTaskId: string | undefined;

        // Step 1: Gather context if needed
        if (this.needsContextGathering(goalLower)) {
            const contextTask = this.createTask(
                'Gather context and current state',
                'query',
                this.selectQueryTool(goalLower),
                prevTaskId ? [prevTaskId] : []
            );
            tasks.push(contextTask);
            prevTaskId = contextTask.id;
        }

        // Step 2: Main actions
        for (const tool of analysis.requiredTools) {
            if (tool.startsWith('search') || tool.startsWith('get_')) {
                continue; // Skip query tools in main loop
            }

            const actionTask = this.createTask(
                `Execute ${tool}`,
                'action',
                tool,
                prevTaskId ? [prevTaskId] : []
            );
            tasks.push(actionTask);
            prevTaskId = actionTask.id;
        }

        // Step 3: Verification
        const verifyTask = this.createTask(
            'Verify changes',
            'verification',
            undefined,
            prevTaskId ? [prevTaskId] : []
        );
        tasks.push(verifyTask);

        return tasks;
    }

    /**
     * Creates a single task.
     */
    private createTask(
        description: string,
        type: Task['type'],
        tool?: string,
        dependencies: string[] = []
    ): Task {
        return {
            id: this.generateId(),
            description,
            type,
            status: 'pending',
            tool,
            dependencies,
            createdAt: Date.now(),
            retryCount: 0,
            maxRetries: this.maxRetries
        };
    }

    /**
     * Determines if the goal needs context gathering first.
     */
    private needsContextGathering(goal: string): boolean {
        const contextPatterns = [
            'update', 'modify', 'link', 'connect', 'move', 
            'organize', 'refactor', 'summarize'
        ];
        return contextPatterns.some(p => goal.includes(p));
    }

    /**
     * Selects appropriate query tool for context gathering.
     */
    private selectQueryTool(goal: string): string {
        if (goal.includes('tag')) return 'search_by_tag';
        if (goal.includes('recent')) return 'get_recent_files';
        if (goal.includes('structure')) return 'get_vault_structure';
        return 'search_vault';
    }

    // ============================================
    // PLAN EXECUTION
    // ============================================

    /**
     * Gets the next executable task from a plan.
     */
    getNextTask(planId: string): Task | null {
        const plan = this.activePlans.get(planId);
        if (!plan || plan.status !== 'executing') return null;

        for (const task of plan.tasks) {
            if (task.status !== 'pending') continue;

            // Check if dependencies are satisfied
            const depsComplete = task.dependencies.every(depId => {
                const dep = plan.tasks.find(t => t.id === depId);
                return dep && dep.status === 'completed';
            });

            if (depsComplete) {
                return task;
            }
        }

        return null;
    }

    /**
     * Starts executing a plan.
     */
    startPlan(planId: string): boolean {
        const plan = this.activePlans.get(planId);
        if (!plan || plan.status !== 'planning') return false;

        plan.status = 'executing';
        return true;
    }

    /**
     * Pauses a plan.
     */
    pausePlan(planId: string): boolean {
        const plan = this.activePlans.get(planId);
        if (!plan || plan.status !== 'executing') return false;

        plan.status = 'paused';
        return true;
    }

    /**
     * Resumes a paused plan.
     */
    resumePlan(planId: string): boolean {
        const plan = this.activePlans.get(planId);
        if (!plan || plan.status !== 'paused') return false;

        plan.status = 'executing';
        return true;
    }

    /**
     * Marks a task as completed.
     */
    completeTask(planId: string, taskId: string, result: string): void {
        const plan = this.activePlans.get(planId);
        if (!plan) return;

        const task = plan.tasks.find(t => t.id === taskId);
        if (!task) return;

        task.status = 'completed';
        task.result = result;
        task.completedAt = Date.now();

        // Check if plan is complete
        const allComplete = plan.tasks.every(t => 
            t.status === 'completed' || t.status === 'failed'
        );

        if (allComplete) {
            this.finishPlan(planId, true);
        }
    }

    /**
     * Marks a task as failed.
     */
    failTask(planId: string, taskId: string, error: string): boolean {
        const plan = this.activePlans.get(planId);
        if (!plan) return false;

        const task = plan.tasks.find(t => t.id === taskId);
        if (!task) return false;

        task.retryCount++;
        
        if (task.retryCount >= task.maxRetries) {
            task.status = 'failed';
            task.error = error;
            
            // Fail dependent tasks
            this.failDependentTasks(plan, taskId);
            
            // Check if plan should fail
            const criticalFailure = task.type === 'action';
            if (criticalFailure) {
                this.finishPlan(planId, false);
            }
            
            return false; // No more retries
        }

        return true; // Can retry
    }

    /**
     * Fails all tasks that depend on a failed task.
     */
    private failDependentTasks(plan: Plan, failedTaskId: string): void {
        for (const task of plan.tasks) {
            if (task.dependencies.includes(failedTaskId) && task.status === 'pending') {
                task.status = 'blocked';
                task.error = `Blocked by failed task: ${failedTaskId}`;
            }
        }
    }

    /**
     * Finishes a plan (success or failure).
     */
    private finishPlan(planId: string, success: boolean): void {
        const plan = this.activePlans.get(planId);
        if (!plan) return;

        plan.status = success ? 'completed' : 'failed';
        plan.completedAt = Date.now();

        // Archive the plan
        this.completedPlans.push(plan);
        this.activePlans.delete(planId);

        // Remember the outcome
        this.memoryManager.remember(
            `Plan "${plan.goal}" ${success ? 'completed successfully' : 'failed'}`,
            'insight',
            { importance: 0.6, tags: ['plan-outcome'] }
        );
    }

    // ============================================
    // PLAN QUERIES
    // ============================================

    /**
     * Gets a plan by ID.
     */
    getPlan(planId: string): Plan | undefined {
        return this.activePlans.get(planId) || 
               this.completedPlans.find(p => p.id === planId);
    }

    /**
     * Gets all active plans.
     */
    getActivePlans(): Plan[] {
        return Array.from(this.activePlans.values());
    }

    /**
     * Gets plan progress.
     */
    getPlanProgress(planId: string): {
        total: number;
        completed: number;
        failed: number;
        pending: number;
        progress: number;
    } | null {
        const plan = this.getPlan(planId);
        if (!plan) return null;

        const completed = plan.tasks.filter(t => t.status === 'completed').length;
        const failed = plan.tasks.filter(t => t.status === 'failed').length;
        const pending = plan.tasks.filter(t => t.status === 'pending' || t.status === 'in_progress').length;

        return {
            total: plan.tasks.length,
            completed,
            failed,
            pending,
            progress: plan.tasks.length > 0 ? (completed / plan.tasks.length) * 100 : 0
        };
    }

    /**
     * Gets a summary of a plan suitable for display.
     */
    getPlanSummary(planId: string): string {
        const plan = this.getPlan(planId);
        if (!plan) return 'Plan not found';

        const progress = this.getPlanProgress(planId);
        if (!progress) return 'Unable to get progress';

        let summary = `**Plan:** ${plan.goal}\n`;
        summary += `**Status:** ${plan.status}\n`;
        summary += `**Progress:** ${progress.completed}/${progress.total} tasks (${progress.progress.toFixed(0)}%)\n\n`;
        summary += `**Tasks:**\n`;

        for (const task of plan.tasks) {
            const statusIcon = this.getStatusIcon(task.status);
            summary += `${statusIcon} ${task.description}`;
            if (task.result) {
                summary += ` → ${task.result.substring(0, 50)}...`;
            }
            if (task.error) {
                summary += ` ⚠ ${task.error}`;
            }
            summary += '\n';
        }

        return summary;
    }

    /**
     * Gets icon for task status.
     */
    private getStatusIcon(status: TaskStatus): string {
        const icons: Record<TaskStatus, string> = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌',
            'blocked': '🚫'
        };
        return icons[status] || '❓';
    }

    // ============================================
    // INTELLIGENT PLANNING
    // ============================================

    /**
     * Suggests an action plan for a complex request.
     */
    suggestPlan(request: string): string {
        const analysis = this.analyzeGoal(request);

        let suggestion = `**Goal Analysis:**\n`;
        suggestion += `- Complexity: ${analysis.complexity}\n`;
        suggestion += `- Estimated steps: ${analysis.estimatedSteps}\n\n`;

        suggestion += `**Required Tools:**\n`;
        for (const tool of analysis.requiredTools) {
            suggestion += `- ${tool}\n`;
        }

        suggestion += `\n**Suggested Plan:**\n`;
        for (let i = 0; i < analysis.suggestedSteps.length; i++) {
            suggestion += `${i + 1}. ${analysis.suggestedSteps[i]}\n`;
        }

        if (analysis.potentialRisks.length > 0) {
            suggestion += `\n**⚠ Potential Risks:**\n`;
            for (const risk of analysis.potentialRisks) {
                suggestion += `- ${risk}\n`;
            }
        }

        return suggestion;
    }

    /**
     * Creates a plan with user confirmation.
     */
    proposeAndCreatePlan(goal: string): { 
        proposal: string; 
        plan: Plan;
        requiresConfirmation: boolean 
    } {
        const analysis = this.analyzeGoal(goal);
        const plan = this.createPlan(goal);
        const proposal = this.getPlanSummary(plan.id);

        return {
            proposal,
            plan,
            requiresConfirmation: analysis.complexity !== 'simple' || analysis.potentialRisks.length > 0
        };
    }

    // ============================================
    // UTILITIES
    // ============================================

    /**
     * Generates a unique ID.
     */
    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    }

    /**
     * Clears completed plans older than specified days.
     */
    cleanupOldPlans(days: number = 7): number {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        const before = this.completedPlans.length;
        
        this.completedPlans = this.completedPlans.filter(p => 
            (p.completedAt || p.createdAt) > cutoff
        );

        return before - this.completedPlans.length;
    }

    /**
     * Gets statistics about planning.
     */
    getStats(): {
        activePlans: number;
        completedPlans: number;
        successRate: number;
    } {
        const completed = this.completedPlans.filter(p => p.status === 'completed').length;
        const failed = this.completedPlans.filter(p => p.status === 'failed').length;
        const total = completed + failed;

        return {
            activePlans: this.activePlans.size,
            completedPlans: this.completedPlans.length,
            successRate: total > 0 ? (completed / total) * 100 : 0
        };
    }
}
