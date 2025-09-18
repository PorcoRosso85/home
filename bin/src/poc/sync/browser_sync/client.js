/**
 * Browser Sync Client
 * WebSocket経由でサーバーと同期
 */

class SyncClient {
    constructor() {
        this.ws = null;
        this.clientId = null;
        this.reconnectInterval = null;
        this.state = {
            editor: '',
            todos: new Map()
        };
        
        this.initializeUI();
        this.connect();
    }
    
    initializeUI() {
        // エディタ
        this.editor = document.getElementById('sharedEditor');
        this.editor.addEventListener('input', this.debounce(() => {
            this.sendEvent('UPDATE', {
                type: 'editor',
                content: this.editor.value
            });
        }, 300));
        
        // TODOフォーム
        document.getElementById('todoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('todoInput');
            const text = input.value.trim();
            if (text) {
                const todoId = `todo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                this.sendEvent('CREATE', {
                    type: 'todo',
                    id: todoId,
                    text,
                    completed: false
                });
                input.value = '';
            }
        });
    }
    
    connect() {
        this.updateStatus('connecting');
        
        try {
            this.ws = new WebSocket('ws://localhost:8080');
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateStatus('connected');
                
                // 再接続タイマーをクリア
                if (this.reconnectInterval) {
                    clearInterval(this.reconnectInterval);
                    this.reconnectInterval = null;
                }
                
                // 初期状態を取得
                this.ws.send(JSON.stringify({ type: 'get_state' }));
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected');
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected');
            };
            
        } catch (error) {
            console.error('Connection error:', error);
            this.updateStatus('disconnected');
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        if (!this.reconnectInterval) {
            this.reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                this.connect();
            }, 3000);
        }
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'connected':
                this.clientId = message.clientId;
                document.getElementById('clientId').textContent = this.clientId;
                this.logEvent(`Connected as ${this.clientId}`);
                break;
                
            case 'sync_event':
                this.handleSyncEvent(message.event);
                break;
                
            case 'event_sent':
                this.logEvent(`Event sent: ${message.event.operation} ${message.event.data.type}`);
                break;
                
            case 'state_response':
                this.rebuildState(message.events);
                break;
                
            case 'error':
                console.error('Server error:', message.message);
                this.logEvent(`Error: ${message.message}`);
                break;
        }
    }
    
    handleSyncEvent(event) {
        const { operation, data } = event;
        
        // 自分が送信したイベントは無視（すでに反映済み）
        if (event.clientId === this.clientId) {
            return;
        }
        
        this.logEvent(`Received: ${operation} ${data.type} from ${event.clientId}`);
        
        switch (data.type) {
            case 'editor':
                this.updateEditor(data.content);
                break;
                
            case 'todo':
                this.updateTodo(operation, data);
                break;
        }
    }
    
    rebuildState(events) {
        // 状態をクリア
        this.state.editor = '';
        this.state.todos.clear();
        
        // イベントを再生して状態を再構築
        events.forEach(event => {
            const { operation, data } = event;
            
            switch (data.type) {
                case 'editor':
                    if (operation === 'UPDATE') {
                        this.state.editor = data.content;
                    }
                    break;
                    
                case 'todo':
                    if (operation === 'CREATE') {
                        this.state.todos.set(data.id, {
                            text: data.text,
                            completed: false
                        });
                    } else if (operation === 'UPDATE') {
                        const todo = this.state.todos.get(data.id);
                        if (todo) {
                            todo.completed = data.completed;
                        }
                    } else if (operation === 'DELETE') {
                        this.state.todos.delete(data.id);
                    }
                    break;
            }
        });
        
        // UIを更新
        this.updateEditor(this.state.editor);
        this.renderTodos();
    }
    
    updateEditor(content) {
        if (this.editor.value !== content) {
            this.editor.value = content;
        }
    }
    
    updateTodo(operation, data) {
        switch (operation) {
            case 'CREATE':
                this.state.todos.set(data.id, {
                    text: data.text,
                    completed: false
                });
                this.renderTodos();
                break;
                
            case 'UPDATE':
                const todo = this.state.todos.get(data.id);
                if (todo) {
                    todo.completed = data.completed;
                    this.renderTodos();
                }
                break;
                
            case 'DELETE':
                this.state.todos.delete(data.id);
                this.renderTodos();
                break;
        }
    }
    
    renderTodos() {
        const todoList = document.getElementById('todoList');
        todoList.innerHTML = '';
        
        this.state.todos.forEach((todo, id) => {
            const li = document.createElement('li');
            li.className = `todo-item ${todo.completed ? 'completed' : ''}`;
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = todo.completed;
            checkbox.addEventListener('change', () => {
                this.sendEvent('UPDATE', {
                    type: 'todo',
                    id,
                    completed: checkbox.checked
                });
            });
            
            const span = document.createElement('span');
            span.textContent = todo.text;
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'todo-delete';
            deleteBtn.textContent = '削除';
            deleteBtn.addEventListener('click', () => {
                this.sendEvent('DELETE', {
                    type: 'todo',
                    id
                });
            });
            
            li.appendChild(checkbox);
            li.appendChild(span);
            li.appendChild(deleteBtn);
            todoList.appendChild(li);
        });
    }
    
    sendEvent(operation, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // 楽観的更新
            this.handleSyncEvent({ operation, data, clientId: this.clientId });
            
            // サーバーに送信
            this.ws.send(JSON.stringify({
                type: 'send_event',
                operation,
                data
            }));
        }
    }
    
    updateStatus(status) {
        const indicator = document.getElementById('statusIndicator');
        const text = document.getElementById('statusText');
        
        indicator.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                text.textContent = '接続済み';
                break;
            case 'disconnected':
                text.textContent = '切断中';
                break;
            case 'connecting':
                text.textContent = '接続中...';
                break;
        }
    }
    
    logEvent(message) {
        const log = document.getElementById('eventLog');
        const entry = document.createElement('div');
        entry.className = 'event-entry';
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        log.insertBefore(entry, log.firstChild);
        
        // ログが多くなりすぎないように制限
        while (log.children.length > 50) {
            log.removeChild(log.lastChild);
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// アプリケーション起動
const client = new SyncClient();