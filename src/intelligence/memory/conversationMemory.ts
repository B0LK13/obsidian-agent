/**
 * Conversation Memory - Maintains context within a session
 */

export interface Message {
role: 'user' | 'agent';
content: string;
timestamp: number;
metadata?: {
tools_used?: string[];
confidence?: number;
intent?: string;
};
}

export interface ConversationContext {
messages: Message[];
goals: string[];
mentioned_notes: string[];
mentioned_concepts: string[];
unresolved_questions: string[];
user_preferences: Map<string, string>;
}

export class ConversationMemory {
private context: ConversationContext;
private maxMessages: number = 20;
private maxAge: number = 3600000; // 1 hour in ms

constructor() {
this.context = {
messages: [],
goals: [],
mentioned_notes: [],
mentioned_concepts: [],
unresolved_questions: [],
user_preferences: new Map()
};
}

addMessage(role: 'user' | 'agent', content: string, metadata?: any): void {
const message: Message = {
role,
content,
timestamp: Date.now(),
metadata
};

this.context.messages.push(message);
this.extractGoals(content);
this.extractMentions(content);
this.extractQuestions(content, role);
this.pruneOldMessages();
}

private extractGoals(content: string): void {
const goalPatterns = [
/I (?:want|need) to (.+?)(?:\.|$)/gi,
/(?:help me|I'm trying to) (.+?)(?:\.|$)/gi,
/my goal is to (.+?)(?:\.|$)/gi,
/I'm working on (.+?)(?:\.|$)/gi
];

for (const pattern of goalPatterns) {
const matches = content.matchAll(pattern);
for (const match of matches) {
const goal = match[1].trim();
if (goal.length > 5 && !this.context.goals.includes(goal)) {
this.context.goals.push(goal);
}
}
}

if (this.context.goals.length > 5) {
this.context.goals = this.context.goals.slice(-5);
}
}

private extractMentions(content: string): void {
const noteMatches = content.matchAll(/\[\[([^\]]+)\]\]/g);
for (const match of noteMatches) {
const note = match[1];
if (!this.context.mentioned_notes.includes(note)) {
this.context.mentioned_notes.push(note);
}
}

const conceptMatches = content.matchAll(/"([^"]+)"/g);
for (const match of conceptMatches) {
const concept = match[1];
if (concept.length > 3 && !this.context.mentioned_concepts.includes(concept)) {
this.context.mentioned_concepts.push(concept);
}
}

if (this.context.mentioned_notes.length > 10) {
this.context.mentioned_notes = this.context.mentioned_notes.slice(-10);
}
if (this.context.mentioned_concepts.length > 10) {
this.context.mentioned_concepts = this.context.mentioned_concepts.slice(-10);
}
}

private extractQuestions(content: string, role: 'user' | 'agent'): void {
if (role === 'user') {
if (content.includes('?')) {
const questions = content.split('?').filter(q => q.trim().length > 5);
for (const q of questions) {
const question = q.trim() + '?';
if (!this.context.unresolved_questions.includes(question)) {
this.context.unresolved_questions.push(question);
}
}
}
} else {
this.context.unresolved_questions = this.context.unresolved_questions.filter(_q => {
return content.length < 200 || content.includes('clarify') || content.includes('not sure');
});
}

if (this.context.unresolved_questions.length > 3) {
this.context.unresolved_questions = this.context.unresolved_questions.slice(-3);
}
}

private pruneOldMessages(): void {
const now = Date.now();

this.context.messages = this.context.messages.filter(msg => 
now - msg.timestamp < this.maxAge
);

if (this.context.messages.length > this.maxMessages) {
this.context.messages = this.context.messages.slice(-this.maxMessages);
}
}

learnPreference(key: string, value: string): void {
this.context.user_preferences.set(key, value);
}

getPreference(key: string): string | undefined {
return this.context.user_preferences.get(key);
}

getSummary(): string {
let summary = '';

if (this.context.goals.length > 0) {
summary += `User goals: ${this.context.goals.join(', ')}\n`;
}

if (this.context.mentioned_notes.length > 0) {
summary += `Discussed notes: ${this.context.mentioned_notes.map(n => `[[${n}]]`).join(', ')}\n`;
}

if (this.context.mentioned_concepts.length > 0) {
summary += `Key concepts: ${this.context.mentioned_concepts.join(', ')}\n`;
}

if (this.context.unresolved_questions.length > 0) {
summary += `Unresolved: ${this.context.unresolved_questions.join('; ')}\n`;
}

return summary;
}

getContext(): string {
const summary = this.getSummary();
if (!summary) return '';

return `\n[Session Context]\n${summary}\n`;
}

getHistory(count: number = 5): Message[] {
return this.context.messages.slice(-count);
}

wasDiscussed(topic: string): boolean {
const lowerTopic = topic.toLowerCase();

if (this.context.mentioned_notes.some(n => n.toLowerCase().includes(lowerTopic))) {
return true;
}

if (this.context.mentioned_concepts.some(c => c.toLowerCase().includes(lowerTopic))) {
return true;
}

const recentMessages = this.getHistory(10);
return recentMessages.some(msg => msg.content.toLowerCase().includes(lowerTopic));
}

getCurrentGoal(): string | undefined {
return this.context.goals[this.context.goals.length - 1];
}

clear(): void {
this.context = {
messages: [],
goals: [],
mentioned_notes: [],
mentioned_concepts: [],
unresolved_questions: [],
user_preferences: new Map()
};
}

export(): any {
return {
...this.context,
user_preferences: Array.from(this.context.user_preferences.entries())
};
}

import(data: any): void {
this.context = {
...data,
user_preferences: new Map(data.user_preferences || [])
};
}
}

