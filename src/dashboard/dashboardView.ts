import { ItemView, WorkspaceLeaf, TFile, Notice } from 'obsidian';
import ObsidianAgent from '../../main';
import { DashboardData, StatCard, ActivityItem, ModelStatus } from './dashboardData';

export const DASHBOARD_VIEW_TYPE = 'obsidian-agent-dashboard';
export const DASHBOARD_VIEW_ICON = 'layout-dashboard';

export class DashboardView extends ItemView {
    private plugin: ObsidianAgent;
    private data: DashboardData;
    private refreshInterval: number | null = null;

    constructor(leaf: WorkspaceLeaf, plugin: ObsidianAgent) {
        super(leaf);
        this.plugin = plugin;
        this.data = new DashboardData();
    }

    getViewType(): string {
        return DASHBOARD_VIEW_TYPE;
    }

    getDisplayText(): string {
        return 'Agent Dashboard';
    }

    getIcon(): string {
        return DASHBOARD_VIEW_ICON;
    }

    async onOpen(): Promise<void> {
        this.containerEl.empty();
        this.containerEl.addClass('obsidian-agent-dashboard');
        
        await this.render();
        this.startAutoRefresh();
    }

    async onClose(): Promise<void> {
        this.stopAutoRefresh();
    }

    private startAutoRefresh(): void {
        this.refreshInterval = window.setInterval(() => {
            this.updateData();
            this.refreshStats();
        }, 5000);
    }

    private stopAutoRefresh(): void {
        if (this.refreshInterval) {
            window.clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    private async updateData(): Promise<void> {
        // Update stats from plugin services
        this.data.updateStats({
            totalNotes: this.app.vault.getMarkdownFiles().length,
            aiCalls: this.plugin.aiService?.getCallCount() || 0,
            tokensUsed: this.plugin.aiService?.getTotalTokens() || 0,
            cacheHits: this.plugin.cacheService?.getHits() || 0,
            avgResponseTime: this.plugin.aiService?.getAvgResponseTime() || 0,
            activeModels: this.getActiveModels()
        });
    }

    private getActiveModels(): ModelStatus[] {
        const settings = this.plugin.settings;
        const models: ModelStatus[] = [];

        if (settings.openaiApiKey) {
            models.push({
                name: settings.model || 'gpt-4',
                provider: 'OpenAI',
                status: 'active',
                icon: 'brain-circuit'
            });
        }

        if (settings.anthropicApiKey) {
            models.push({
                name: settings.anthropicModel || 'claude-3-opus',
                provider: 'Anthropic',
                status: 'active',
                icon: 'sparkles'
            });
        }

        if (settings.useOllama) {
            models.push({
                name: settings.ollamaModel || 'llama2',
                provider: 'Ollama',
                status: 'active',
                icon: 'server'
            });
        }

        if (settings.customApiUrl) {
            models.push({
                name: 'Custom API',
                provider: 'Custom',
                status: 'active',
                icon: 'plug'
            });
        }

        return models;
    }

    private async render(): Promise<void> {
        const container = this.containerEl.createDiv({ cls: 'dashboard-container' });

        // Header
        const header = container.createDiv({ cls: 'dashboard-header' });
        header.createEl('h1', { text: 'Obsidian Agent', cls: 'dashboard-title' });
        header.createEl('span', { 
            text: 'AI-Powered Knowledge Management', 
            cls: 'dashboard-subtitle' 
        });

        // Quick Actions Bar
        const actionsBar = container.createDiv({ cls: 'dashboard-actions' });
        const quickActions = [
            { label: 'New Chat', icon: 'message-square-plus', action: () => this.openNewChat() },
            { label: 'Summarize', icon: 'file-text', action: () => this.runCommand('generate-summary') },
            { label: 'Settings', icon: 'settings', action: () => this.openSettings() },
            { label: 'Refresh', icon: 'refresh-cw', action: () => this.refreshDashboard() }
        ];

        quickActions.forEach(action => {
            const btn = actionsBar.createEl('button', { cls: 'dashboard-action-btn' });
            btn.setAttribute('aria-label', action.label);
            btn.innerHTML = `<svg viewBox="0 0 24 24" class="icon"><use href="#${action.icon}"></use></svg><span>${action.label}</span>`;
            btn.addEventListener('click', action.action);
        });

        // Stats Grid
        const statsGrid = container.createDiv({ cls: 'dashboard-stats-grid' });
        
        const statCards: StatCard[] = [
            { 
                title: 'Total Notes', 
                value: this.data.stats.totalNotes.toString(), 
                icon: 'files',
                trend: '+12%',
                trendUp: true,
                color: 'blue'
            },
            { 
                title: 'AI Interactions', 
                value: this.data.stats.aiCalls.toString(), 
                icon: 'message-circle',
                trend: '+8%',
                trendUp: true,
                color: 'purple'
            },
            { 
                title: 'Tokens Used', 
                value: this.formatNumber(this.data.stats.tokensUsed), 
                icon: 'hash',
                trend: '+24%',
                trendUp: true,
                color: 'green'
            },
            { 
                title: 'Cache Hits', 
                value: this.data.stats.cacheHits.toString(), 
                icon: 'zap',
                trend: '+5%',
                trendUp: true,
                color: 'orange'
            }
        ];

        statCards.forEach(card => {
            const cardEl = statsGrid.createDiv({ cls: `stat-card stat-card-${card.color}` });
            
            const cardHeader = cardEl.createDiv({ cls: 'stat-card-header' });
            cardHeader.createDiv({ cls: 'stat-icon-wrapper', text: this.getIconSvg(card.icon) });
            
            const trendEl = cardHeader.createDiv({ 
                cls: `stat-trend ${card.trendUp ? 'trend-up' : 'trend-down'}`,
                text: card.trend 
            });

            cardEl.createEl('h3', { text: card.value, cls: 'stat-value' });
            cardEl.createEl('p', { text: card.title, cls: 'stat-label' });
        });

        // Main Content Area
        const mainContent = container.createDiv({ cls: 'dashboard-main' });

        // Left Column - Activity & Models
        const leftColumn = mainContent.createDiv({ cls: 'dashboard-column' });
        
        // Active Models Section
        const modelsSection = leftColumn.createDiv({ cls: 'dashboard-section' });
        modelsSection.createEl('h2', { text: 'Active Models', cls: 'section-title' });
        
        const modelsList = modelsSection.createDiv({ cls: 'models-list' });
        this.data.stats.activeModels.forEach(model => {
            const modelEl = modelsList.createDiv({ cls: 'model-item' });
            modelEl.innerHTML = `
                <div class="model-icon">${this.getIconSvg(model.icon)}</div>
                <div class="model-info">
                    <span class="model-name">${model.name}</span>
                    <span class="model-provider">${model.provider}</span>
                </div>
                <span class="model-status status-${model.status}">${model.status}</span>
            `;
        });

        // Recent Activity Section
        const activitySection = leftColumn.createDiv({ cls: 'dashboard-section' });
        activitySection.createEl('h2', { text: 'Recent Activity', cls: 'section-title' });
        
        const activityList = activitySection.createDiv({ cls: 'activity-list' });
        this.data.recentActivity.forEach(activity => {
            const activityEl = activityList.createDiv({ cls: 'activity-item' });
            activityEl.innerHTML = `
                <div class="activity-icon ${activity.type}">${this.getIconSvg(activity.icon)}</div>
                <div class="activity-content">
                    <span class="activity-title">${activity.title}</span>
                    <span class="activity-time">${activity.time}</span>
                </div>
            `;
        });

        // Right Column - Analytics & Quick Tools
        const rightColumn = mainContent.createDiv({ cls: 'dashboard-column' });

        // Performance Metrics
        const perfSection = rightColumn.createDiv({ cls: 'dashboard-section' });
        perfSection.createEl('h2', { text: 'Performance', cls: 'section-title' });
        
        const perfMetrics = perfSection.createDiv({ cls: 'perf-metrics' });
        
        // Response Time Gauge
        const responseMetric = perfMetrics.createDiv({ cls: 'perf-metric' });
        responseMetric.innerHTML = `
            <div class="metric-header">
                <span class="metric-label">Avg Response Time</span>
                <span class="metric-value">${this.data.stats.avgResponseTime.toFixed(2)}s</span>
            </div>
            <div class="metric-bar">
                <div class="metric-fill" style="width: ${Math.min(this.data.stats.avgResponseTime * 20, 100)}%"></div>
            </div>
        `;

        // Token Usage Chart (simplified visual)
        const tokenSection = rightColumn.createDiv({ cls: 'dashboard-section' });
        tokenSection.createEl('h2', { text: 'Token Usage', cls: 'section-title' });
        
        const tokenChart = tokenSection.createDiv({ cls: 'token-chart' });
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const values = [65, 78, 45, 89, 102, 56, 73];
        const maxVal = Math.max(...values);
        
        days.forEach((day, i) => {
            const bar = tokenChart.createDiv({ cls: 'chart-bar' });
            bar.innerHTML = `
                <div class="chart-fill" style="height: ${(values[i] / maxVal) * 100}%"></div>
                <span class="chart-label">${day}</span>
            `;
        });

        // Quick Tools Section
        const toolsSection = rightColumn.createDiv({ cls: 'dashboard-section' });
        toolsSection.createEl('h2', { text: 'Quick Tools', cls: 'section-title' });
        
        const toolsGrid = toolsSection.createDiv({ cls: 'tools-grid' });
        const tools = [
            { name: 'Expand Ideas', icon: 'expand', command: 'expand-ideas' },
            { name: 'Improve Writing', icon: 'edit-3', command: 'improve-writing' },
            { name: 'Generate Outline', icon: 'list', command: 'generate-outline' },
            { name: 'Ask Question', icon: 'help-circle', command: 'ask-question' }
        ];

        tools.forEach(tool => {
            const toolBtn = toolsGrid.createEl('button', { cls: 'tool-btn' });
            toolBtn.innerHTML = `
                <span class="tool-icon">${this.getIconSvg(tool.icon)}</span>
                <span class="tool-name">${tool.name}</span>
            `;
            toolBtn.addEventListener('click', () => this.runCommand(tool.command));
        });

        // System Status Footer
        const footer = container.createDiv({ cls: 'dashboard-footer' });
        footer.innerHTML = `
            <div class="system-status">
                <span class="status-indicator status-online"></span>
                <span>System Operational</span>
            </div>
            <div class="version-info">
                v${this.plugin.manifest.version}
            </div>
        `;
    }

    private refreshStats(): void {
        // Update stat values without full re-render
        const statValues = this.containerEl.querySelectorAll('.stat-value');
        if (statValues.length >= 4) {
            statValues[0].textContent = this.data.stats.totalNotes.toString();
            statValues[1].textContent = this.data.stats.aiCalls.toString();
            statValues[2].textContent = this.formatNumber(this.data.stats.tokensUsed);
            statValues[3].textContent = this.data.stats.cacheHits.toString();
        }
    }

    private refreshDashboard(): void {
        this.updateData().then(() => {
            this.containerEl.empty();
            this.render();
            new Notice('Dashboard refreshed');
        });
    }

    private openNewChat(): void {
        this.plugin.openAgentModal();
    }

    private openSettings(): void {
        (this.app as any).setting.open();
        (this.app as any).setting.openTabById('obsidian-agent');
    }

    private async runCommand(command: string): Promise<void> {
        await this.plugin.handleDashboardCommand(command);
    }

    private formatNumber(num: number): string {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    private getIconSvg(iconName: string): string {
        const icons: Record<string, string> = {
            'files': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>',
            'message-circle': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
            'hash': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/></svg>',
            'zap': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
            'brain-circuit': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/></svg>',
            'sparkles': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
            'server': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg>',
            'plug': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-5"/><path d="M15 8V2"/><path d="M15 8a3 3 0 0 0-3 3v6a3 3 0 0 0 3 3 5 5 0 0 0 5-5v-4a5 5 0 0 0-5-5Z"/><path d="M9 8V2"/><path d="M9 8a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3 5 5 0 0 1-5-5v-4a5 5 0 0 1 5-5Z"/></svg>',
            'message-square-plus': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M12 7v6"/><path d="M9 10h6"/></svg>',
            'file-text': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
            'settings': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
            'refresh-cw': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
            'expand': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21 21-6-6m6 6v-4.8m0 4.8h-4.8"/><path d="M3 16.2V21m0 0h4.8M3 21l6-6"/><path d="M21 7.8V3m0 0h-4.8M21 3l-6 6"/><path d="M3 7.8V3m0 0h4.8M3 3l6 6"/></svg>',
            'edit-3': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
            'list': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
            'help-circle': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>',
            'layout-dashboard': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>'
        };
        
        return icons[iconName] || icons['files'];
    }
}
