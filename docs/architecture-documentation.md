# Architecture Documentation

## Executive Summary

File Search is a cross-platform desktop application built with Python and PyQt6 that provides fast, extensible file searching capabilities. The application implements a modular architecture with plugin support, multi-threaded search operations, and a modern user interface with comprehensive file management features.

### Key Features
- **High Performance**: Multi-threaded search with sub-2-second target for typical directories
- **Cross-Platform**: Native support for Windows, macOS, and Linux
- **Extensible**: Plugin architecture for custom search providers and result processors
- **User-Friendly**: Modern PyQt6 interface with advanced search controls
- **Comprehensive**: File operations, sorting, filtering, and export capabilities

### Success Criteria
- Search performance under 2 seconds for typical directory structures
- Cross-platform compatibility maintained across all supported operating systems
- Zero crashes during search operations with robust error handling
- Clean, maintainable, and extensible codebase architecture

## Technology Stack

### Core Technologies

| Category | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Language** | Python | 3.9+ | Core application logic and cross-platform compatibility |
| **GUI Framework** | PyQt6 | >=6.6.0 | Cross-platform desktop interface with native performance |
| **Logging** | loguru | >=0.7.2 | Structured logging with rotation and compression |
| **File Paths** | platformdirs | >=4.0.0 | Cross-platform configuration and data directories |
| **Sorting** | natsort | latest | Natural sorting of search results |
| **Testing** | pytest | >=7.4.0 | Testing framework with pytest-qt for UI testing |
| **Code Quality** | black, flake8, pre-commit | latest | Code formatting, linting, and automated checks |
| **Packaging** | setuptools | modern | Python packaging with pyproject.toml configuration |

### Development Tools

| Tool | Configuration | Purpose |
|-------|-------------|---------|
| **Black** | 88-character line length | Code formatting and consistency |
| **Flake8** | Custom ignore rules (E203, F401) | Linting and code quality |
| **isort** | Black profile | Import sorting and organization |
| **pytest-qt** | Qt API = pyqt6 | GUI testing with Qt event loop |
| **pre-commit** | Automated hooks | Quality gates before commits |

## Architecture Pattern

### Event-Driven Desktop Architecture

File Search implements an **event-driven desktop architecture** using PyQt6's signal/slot mechanism combined with multi-threading for performance and responsiveness.

### Core Architectural Principles

1. **Separation of Concerns**
   - **Core Logic**: Business logic independent of UI presentation
   - **UI Layer**: PyQt6 components focused on user interaction
   - **Plugin System**: Extensibility layer for custom functionality
   - **Data Models**: Type-safe data structures and interfaces

2. **Multi-threaded Design**
   - **Search Operations**: Run in separate QThread workers
   - **UI Responsiveness**: Main thread remains responsive during operations
   - **Thread Safety**: PyQt6 signals/slots ensure thread-safe communication
   - **Progress Indication**: Real-time progress updates via signals

3. **Plugin Architecture**
   - **Abstract Base**: `SearchPlugin` class defines plugin interface
   - **Dynamic Loading**: Runtime plugin discovery and loading
   - **Lifecycle Management**: Initialize, execute, cleanup phases
   - **Configuration**: Plugin-specific configuration support

4. **Configuration Management**
   - **JSON-based**: Human-readable configuration format
   - **Cross-Platform**: platformdirs for OS-specific directories
   - **Runtime Updates**: File watching for configuration changes
   - **Type Safety**: Validation and default value handling

## Component Architecture

### 1. Core Components (`src/filesearch/core/`)

#### SearchEngine
- **Purpose**: Multi-threaded file search with generator-based streaming
- **Pattern**: Concurrent directory traversal with ThreadPoolExecutor
- **Features**:
  - Partial matching with fnmatch patterns
  - Early termination when max results reached
  - Progress indication via PyQt6 signals
  - Cancellation support for long-running searches

#### ConfigManager
- **Purpose**: Cross-platform configuration management
- **Pattern**: Singleton with JSON persistence
- **Features**:
  - Platform-specific config directories
  - File watching for runtime changes
  - Type-safe configuration access
  - Default values with validation

#### SortEngine
- **Purpose**: Result sorting and filtering algorithms
- **Pattern**: Strategy pattern for different sort criteria
- **Features**:
  - Natural sorting via natsort
  - Multiple sort criteria (name, size, date, type)
  - Ascending/descending order
  - Case-sensitive/insensitive options

#### SecurityManager
- **Purpose**: File permissions and security operations
- **Pattern**: Facade for platform-specific security operations
- **Features**:
  - Permission checking and validation
  - Safe file operations with error handling
  - Cross-platform path handling

### 2. UI Components (`src/filesearch/ui/`)

#### MainWindow
- **Purpose**: Primary application window and orchestration
- **Pattern**: Model-View-Controller with PyQt6
- **Features**:
  - Menu bar with File, Edit, View, Help menus
  - Central widget layout management
  - Status bar with progress information
  - Keyboard shortcuts and accessibility

#### ResultsView
- **Purpose**: Search results display with virtual scrolling
- **Pattern**: Custom model/delegate with QAbstractListModel
- **Features**:
  - Virtual scrolling for large result sets
  - Custom item delegate with highlighting
  - Context menu support
  - Multi-selection and drag operations

#### SearchControls
- **Purpose**: Search input, directory selection, and control widgets
- **Pattern**: Composite widgets with signal communication
- **Features**:
  - Advanced search input with history
  - Directory browser with recent directories
  - Search initiation and cancellation
  - Progress indication and status display

### 3. Plugin System (`src/filesearch/plugins/`)

#### PluginManager
- **Purpose**: Plugin discovery, loading, and lifecycle management
- **Pattern**: Registry pattern with dynamic loading
- **Features**:
  - Entry point and directory-based discovery
  - Plugin validation and error handling
  - Configuration integration
  - Runtime plugin management

#### PluginBase
- **Purpose**: Abstract interface for all search plugins
- **Pattern**: Template Method with lifecycle hooks
- **Features**:
  - Standardized plugin interface
  - Configuration and initialization
  - Search execution with context
  - Cleanup and resource management

## Data Architecture

### Data Models

#### SearchResult
```python
@dataclass
class SearchResult:
    path: Path              # File/folder path
    size: int              # Size in bytes (0 for directories)
    modified: float        # Modification timestamp
    plugin_source: Optional[str] = None  # Plugin that provided result
```

#### Configuration Schema
```python
{
    "search": {
        "max_results": 1000,
        "max_workers": 4,
        "case_sensitive": false,
        "use_regex": false
    },
    "ui": {
        "theme": "system",
        "window_size": [800, 600],
        "show_hidden": false
    },
    "plugins": {
        "enabled": [],
        "auto_load": true
    }
}
```

### Data Flow

1. **User Input** → SearchControls → SearchEngine.search()
2. **Search Execution** → ThreadPoolExecutor → File system traversal
3. **Result Streaming** → Generator → ResultsModel → UI update
4. **User Interaction** → UI events → Plugin operations → File operations

## State Management

### PyQt6 Signals/Slots

#### Search State Machine
```python
class SearchState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"
```

#### Key Signals
- **status_update**: Search progress and status changes
- **results_count_update**: Real-time result count updates
- **result_found**: Individual search result notifications
- **error_occurred**: Error handling and reporting

### Configuration Management
- **JSON Persistence**: Human-readable configuration files
- **Platform Directories**: OS-specific config locations
- **Runtime Updates**: File watching for configuration changes
- **Type Safety**: Validation and default value handling

## Performance Architecture

### Multi-threading Strategy

#### Search Workers
- **ThreadPoolExecutor**: Parallel directory traversal
- **Configurable Threads**: Default 4 workers, user configurable
- **Generator Pattern**: Memory-efficient result streaming
- **Cancellation**: Graceful termination support

#### UI Performance
- **Virtual Scrolling**: Handle large result sets efficiently
- **Batch Loading**: Load results in 100-item chunks
- **Lazy Evaluation**: Defer expensive operations
- **Memory Management**: Proper cleanup and garbage collection

### Search Optimization
- **Early Termination**: Stop when max results reached
- **Pattern Matching**: Efficient fnmatch implementation
- **Directory Pruning**: Skip excluded directories early
- **Result Caching**: Optional result caching for repeated searches

## Security Architecture

### File Operations Security
- **Path Validation**: Prevent path traversal attacks
- **Permission Checking**: Validate file access permissions
- **Input Sanitization**: Search query validation and sanitization
- **Error Handling**: Secure error reporting without information leakage

### Plugin Security
- **Sandboxing**: Isolated plugin execution environment
- **Validation**: Plugin metadata and interface validation
- **Permissions**: Limited plugin access to system resources
- **Loading**: Secure plugin loading with error handling

## Testing Architecture

### Test Strategy

#### Unit Testing
- **Isolation**: Test individual components in isolation
- **Mocking**: Mock external dependencies for focused testing
- **Coverage**: Target >80% code coverage
- **Automation**: CI/CD pipeline for automated testing

#### Integration Testing
- **Component Interaction**: Test multi-component workflows
- **Plugin System**: Test plugin loading and execution
- **File Operations**: Test file operations across platforms
- **Configuration**: Test configuration management and persistence

#### UI Testing
- **pytest-qt**: GUI testing with Qt event loop
- **User Interactions**: Test mouse, keyboard, and drag-drop
- **Accessibility**: Test keyboard navigation and screen readers
- **Cross-Platform**: Test UI on different operating systems

## Deployment Architecture

### Packaging Strategy

#### Python Package
- **pyproject.toml**: Modern Python packaging configuration
- **setuptools**: Build backend with wheel generation
- **Dependencies**: Minimal runtime dependencies for fast installation
- **Cross-Platform**: Single package supports all target platforms

#### Distribution Channels
- **PyPI**: Primary distribution channel for Python packages
- **GitHub Releases**: Source and binary distributions
- **Multi-Platform**: Wheels for Windows, macOS, and Linux

### Installation Methods

#### User Installation
```bash
# From PyPI
pip install filesearch

# From Source
git clone https://github.com/filesearch/filesearch.git
cd filesearch
pip install -e .
```

#### Development Installation
```bash
# Clone repository
git clone https://github.com/filesearch/filesearch.git
cd filesearch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Quality Assurance

### Code Quality Standards

#### Style Guidelines
- **Black**: 88-character line length, consistent formatting
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Google-style docstrings for all public functions
- **Naming**: snake_case for files/functions, PascalCase for classes

#### Quality Gates
- **Pre-commit Hooks**: Automated quality checks before commits
- **CI/CD Pipeline**: Multi-platform testing and validation
- **Code Coverage**: Minimum 80% test coverage requirement
- **Performance**: Search performance benchmarks and regression testing

### Monitoring and Observability

#### Logging Strategy
- **Structured Logging**: loguru with JSON format option
- **Log Rotation**: Automatic log rotation and compression
- **Log Levels**: DEBUG, INFO, WARNING, ERROR levels
- **Performance Metrics**: Search timing and result counting

#### Error Handling
- **Graceful Degradation**: Continue operation despite non-critical errors
- **User Feedback**: Clear error messages and recovery options
- **Crash Reporting**: Automatic crash report generation
- **Debug Information**: Detailed debug information for troubleshooting

## Future Architecture Considerations

### Scalability
- **Plugin Ecosystem**: Framework for third-party plugin development
- **Performance Optimization**: Continuous search performance improvements
- **Memory Efficiency**: Ongoing memory usage optimization
- **User Experience**: Enhanced UI/UX based on user feedback

### Extensibility
- **Search Providers**: Support for different search algorithms
- **Result Processors**: Plugin-based result filtering and processing
- **UI Themes**: Theme support and customization options
- **Internationalization**: Multi-language support framework

### Integration
- **System Integration**: File associations and system tray integration
- **Cloud Storage**: Integration with cloud storage providers
- **Network Search**: Network file sharing and search capabilities
- **API Interface**: REST API for remote search operations
