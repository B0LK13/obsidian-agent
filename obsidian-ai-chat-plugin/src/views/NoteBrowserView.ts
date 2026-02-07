import { ItemView, WorkspaceLeaf, TFile, TFolder, Menu, Notice } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export const VIEW_TYPE_NOTE_BROWSER = 'note-browser-view';

interface NoteTreeItem {
	file: TFile | TFolder;
	isFolder: boolean;
	children?: NoteTreeItem[];
	isExpanded?: boolean;
}

export class NoteBrowserView extends ItemView {
	plugin: AIChatNotesPlugin;
	treeContainer: HTMLElement;
	searchInput: HTMLInputElement;
	currentFilter: string = '';
	expandedFolders: Set<string> = new Set();

	constructor(leaf: WorkspaceLeaf, plugin: AIChatNotesPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType() {
		return VIEW_TYPE_NOTE_BROWSER;
	}

	getDisplayText() {
		return 'Note Browser';
	}

	getIcon() {
		return 'book-open';
	}

	async onOpen() {
		const { containerEl } = this;
		containerEl.empty();
		containerEl.addClass('ai-chat-notes-root', 'note-browser-container');
		
		// Header
		const header = containerEl.createDiv({ cls: 'note-browser-header' });
		header.createEl('h3', { text: 'Notes', cls: 'note-browser-title' });
		
		// Search
		this.searchInput = header.createEl('input', {
			type: 'text',
			placeholder: 'Search notes...',
			cls: 'note-browser-search'
		});
		this.searchInput.addEventListener('input', (e) => {
			this.currentFilter = (e.target as HTMLInputElement).value.toLowerCase();
			this.renderTree();
		});
		
		// New note button
		const newNoteBtn = header.createEl('button', {
			cls: 'new-note-btn',
			text: '+ New Note'
		});
		newNoteBtn.addEventListener('click', () => this.createNewNote());
		
		// Tree container
		this.treeContainer = containerEl.createDiv({ cls: 'note-browser-tree' });
		
		// Initial render
		await this.renderTree();
	}

	async onClose() {
		// Cleanup if needed
	}

	async renderTree() {
		this.treeContainer.empty();
		
		const root = this.app.vault.getRoot();
		const tree = this.buildTree(root);
		
		for (const item of tree.children || []) {
			this.renderTreeItem(item, this.treeContainer, 0);
		}
	}

	buildTree(folder: TFolder): NoteTreeItem {
		const children: NoteTreeItem[] = [];
		
		for (const child of folder.children) {
			if (child instanceof TFolder) {
				const childTree = this.buildTree(child);
				if (this.shouldShowItem(childTree)) {
					children.push(childTree);
				}
			} else if (child instanceof TFile && child.extension === 'md') {
				if (this.shouldShowItem({ file: child, isFolder: false })) {
					children.push({ file: child, isFolder: false });
				}
			}
		}
		
		// Sort: folders first, then alphabetically
		children.sort((a, b) => {
			if (a.isFolder && !b.isFolder) return -1;
			if (!a.isFolder && b.isFolder) return 1;
			return a.file.name.localeCompare(b.file.name);
		});
		
		return {
			file: folder,
			isFolder: true,
			children,
			isExpanded: this.expandedFolders.has(folder.path)
		};
	}

	shouldShowItem(item: NoteTreeItem): boolean {
		if (!this.currentFilter) return true;
		
		const name = item.file.name.toLowerCase();
		if (name.includes(this.currentFilter)) return true;
		
		if (item.isFolder && item.children) {
			return item.children.some(child => this.shouldShowItem(child));
		}
		
		return false;
	}

	renderTreeItem(item: NoteTreeItem, container: HTMLElement, depth: number) {
		const itemEl = container.createDiv({ cls: 'note-tree-item' });
		itemEl.style.paddingLeft = `${depth * 16}px`;
		
		if (item.isFolder) {
			// Folder
			const folderEl = itemEl.createDiv({ cls: 'note-folder' });
			const expandIcon = folderEl.createSpan({
				cls: 'expand-icon',
				text: item.isExpanded ? '▼' : '▶'
			});
			const folderIcon = folderEl.createSpan({
				cls: 'folder-icon',
				text: '📁'
			});
			const folderName = folderEl.createSpan({
				cls: 'folder-name',
				text: item.file.name
			});
			
			folderEl.addEventListener('click', (e) => {
				e.stopPropagation();
				this.toggleFolder(item.file.path);
			});
			
			// Context menu
			folderEl.addEventListener('contextmenu', (e) => {
				e.preventDefault();
				this.showFolderContextMenu(e, item.file as TFolder);
			});
			
			// Render children if expanded
			if (item.isExpanded && item.children) {
				const childrenContainer = container.createDiv({ cls: 'note-children' });
				for (const child of item.children) {
					this.renderTreeItem(child, childrenContainer, depth + 1);
				}
			}
		} else {
			// File
			const fileEl = itemEl.createDiv({ cls: 'note-file' });
			const fileIcon = fileEl.createSpan({
				cls: 'file-icon',
				text: '📝'
			});
			const fileName = fileEl.createSpan({
				cls: 'file-name',
				text: item.file.basename
			});
			
			fileEl.addEventListener('click', () => {
				this.app.workspace.openLinkText(item.file.path, '', true);
			});
			
			fileEl.addEventListener('contextmenu', (e) => {
				e.preventDefault();
				this.showFileContextMenu(e, item.file as TFile);
			});
			
			// Drag and drop
			fileEl.setAttribute('draggable', 'true');
			fileEl.addEventListener('dragstart', (e) => {
				e.dataTransfer?.setData('text/plain', item.file.path);
			});
		}
	}

	toggleFolder(path: string) {
		if (this.expandedFolders.has(path)) {
			this.expandedFolders.delete(path);
		} else {
			this.expandedFolders.add(path);
		}
		this.renderTree();
	}

	showFolderContextMenu(e: MouseEvent, folder: TFolder) {
		const menu = new Menu();
		
		menu.addItem((item) => {
			item.setTitle('New Note');
			item.setIcon('file-plus');
			item.onClick(() => this.createNewNoteInFolder(folder));
		});
		
		menu.addItem((item) => {
			item.setTitle('New Folder');
			item.setIcon('folder-plus');
			item.onClick(() => this.createNewFolder(folder));
		});
		
		menu.addSeparator();
		
		menu.addItem((item) => {
			item.setTitle('Collapse All');
			item.setIcon('fold-vertical');
			item.onClick(() => {
				this.expandedFolders.clear();
				this.renderTree();
			});
		});
		
		menu.showAtMouseEvent(e);
	}

	showFileContextMenu(e: MouseEvent, file: TFile) {
		const menu = new Menu();
		
		menu.addItem((item) => {
			item.setTitle('Open');
			item.setIcon('file');
			item.onClick(() => {
				this.app.workspace.openLinkText(file.path, '', true);
			});
		});
		
		menu.addItem((item) => {
			item.setTitle('Ask AI about this');
			item.setIcon('message-circle');
			item.onClick(async () => {
				await this.plugin.askAIAboutNote(file);
			});
		});
		
		menu.addItem((item) => {
			item.setTitle('Add to Chat Context');
			item.setIcon('plus-circle');
			item.onClick(async () => {
				const content = await this.app.vault.read(file);
				this.plugin.activateChatView();
				const leaf = this.app.workspace.getLeavesOfType('ai-chat-view')[0];
				if (leaf && leaf.view) {
					(leaf.view as any).setContextNote(file.name, content);
				}
			});
		});
		
		menu.addSeparator();
		
		menu.addItem((item) => {
			item.setTitle('Copy Path');
			item.setIcon('copy');
			item.onClick(() => {
				navigator.clipboard.writeText(file.path);
				new Notice('Path copied to clipboard');
			});
		});
		
		menu.addItem((item) => {
			item.setTitle('Delete');
			item.setIcon('trash');
			item.onClick(async () => {
				await this.app.vault.delete(file);
				this.renderTree();
			});
		});
		
		menu.showAtMouseEvent(e);
	}

	async createNewNote() {
		const folder = this.app.fileManager.getNewFileParent('');
		await this.createNewNoteInFolder(folder);
	}

	async createNewNoteInFolder(folder: TFolder) {
		const name = `Note-${Date.now()}`;
		const path = `${folder.path}/${name}.md`;
		const file = await this.app.vault.create(path, '# ');
		await this.app.workspace.openLinkText(file.path, '', true);
		this.renderTree();
	}

	async createNewFolder(parent: TFolder) {
		const name = `Folder-${Date.now()}`;
		const path = `${parent.path}/${name}`;
		await this.app.vault.createFolder(path);
		this.expandedFolders.add(parent.path);
		this.renderTree();
	}
}
