# State Management Analysis

## Overview
The File Search application uses PyQt6's built-in signal/slot mechanism for state management, combined with custom state enums and configuration management.

## State Management Patterns

### 1. PyQt6 Signals and Slots
- **Event-driven communication** between UI components and background workers
- **Thread-safe** state updates across main and worker threads
- **Decoupled** architecture with loose coupling between components

### 2. State Enumeration
```python
class SearchState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"
```

### 3. Configuration Management
- **ConfigManager** class for persistent state
- **JSON-based configuration** with cross-platform directory support
- **Runtime configuration** with file watching for changes
- **Default values** with user override capabilities

### 4. Thread-based State
- **QThread** workers for background operations
- **SearchWorker** for file search operations
- **ChecksumWorker** for file property calculations
- **Signal-based progress reporting** and result streaming

## Key Components

### SearchState Enum
- **Purpose**: Manages search operation lifecycle
- **States**: IDLE → RUNNING → COMPLETED/ERROR
- **Usage**: Controls UI behavior and button states

### ConfigManager
- **Purpose**: Persistent configuration and user preferences
- **Storage**: JSON files in platform-specific config directories
- **Features**: File watching, defaults, validation

### PyQt6 Signals
- **status_update**: Search progress and status updates
- **results_count_update**: Real-time result count updates
- **result_found**: Individual search result notifications
- **error_occurred**: Error handling and reporting

## State Flow
1. **Initialization**: ConfigManager loads persistent state
2. **Search Initiated**: SearchState changes to RUNNING
3. **Background Processing**: Worker threads emit progress signals
4. **UI Updates**: Main thread receives signals via slots
5. **Completion**: SearchState changes to COMPLETED
6. **Persistence**: ConfigManager saves user preferences

## Benefits
- **Thread Safety**: PyQt6 signals are thread-safe by design
- **Responsiveness**: Non-blocking UI during operations
- **Separation of Concerns**: Clear distinction between UI and business logic
- **Extensibility**: Easy to add new state consumers and producers
