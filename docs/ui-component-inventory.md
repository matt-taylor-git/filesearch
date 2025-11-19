# UI Component Inventory

## Overview
The File Search application implements a comprehensive PyQt6-based UI with modular components, custom models, and specialized dialogs.

## Main UI Components

### 1. MainWindow
- **Purpose**: Primary application window with menu bar and central widget
- **Features**:
  - Menu bar with File, Edit, View, Help menus
  - Central widget layout for search controls and results
  - Status bar with progress information
  - Context menu support for file operations
- **Key Methods**:
  - `setup_ui()`: Initialize all UI components
  - `setup_menu_bar()`: Create application menus
  - `perform_search()`: Initiate search operations
  - `handle_search_results()`: Process search results

### 2. SearchInputWidget
- **Purpose**: Advanced search input field with history and auto-complete
- **Features**:
  - Search history management
  - Auto-complete suggestions
  - Visual feedback states
  - Drag and drop support
  - Keyboard shortcuts (Ctrl+V, Escape, etc.)
- **Signals**:
  - `search_initiated(str)`: User starts search
  - `text_changed(str)`: Search text changes
  - `escape_pressed()`: User cancels input

### 3. SearchControlWidget
- **Purpose**: Search controls including directory selection and search button
- **Features**:
  - Directory selection with browse button
  - Recent directories dropdown
  - Search initiation controls
  - Directory validation
- **Components**:
  - Directory input field
  - Browse button
  - Recent directories combobox
  - Search button

### 4. ResultsView
- **Purpose**: Display search results with custom rendering
- **Features**:
  - Virtual scrolling for large result sets
  - Custom item delegate with highlighting
  - Context menu support
  - Double-click file opening
  - Multi-selection support
- **Model**: `ResultsModel` with batch loading
- **Delegate**: `ResultsDelegate` for custom rendering

### 5. ProgressWidget
- **Purpose**: Search progress indication
- **Features**:
  - Progress bar with percentage
  - Status text display
  - Cancel button support
  - Animated progress indication

### 6. StatusWidget
- **Purpose**: Search status display
- **Features**:
  - Current search status text
  - Result count display
  - Search duration tracking
  - Error message display

### 7. SortControls
- **Purpose**: Results sorting controls
- **Features**:
  - Sort criteria selection (name, size, date, type)
  - Sort direction toggle (ascending/descending)
  - Natural sorting support
- **Integration**: Works with `SortEngine` for actual sorting logic

## Dialog Components

### 1. SettingsDialog
- **Purpose**: Application settings and preferences
- **Features**:
  - Tabbed interface for different setting categories
  - Search preferences configuration
  - UI theme selection
  - Plugin management interface
  - Configuration validation

### 2. PropertiesDialog
- **Purpose**: File properties display with checksums
- **Features**:
  - File size and path information
  - Modification and creation dates
  - File permissions display
  - Checksum calculation (MD5, SHA1, SHA256)
  - Background checksum calculation

## Data Models

### 1. ResultsModel
- **Purpose**: Custom list model for search results
- **Features**:
  - Virtual scrolling with batch loading
  - Sort integration
  - Filter support
  - Memory-efficient result handling
- **Batch Size**: 100 items per load for smooth scrolling

### 2. SearchResult
- **Purpose**: Data model for individual search results
- **Fields**:
  - `path`: File path (Path object)
  - `size`: File size in bytes
  - `modified`: Modification timestamp
  - `plugin_source`: Plugin that provided result
- **Display Methods**:
  - `get_display_name()`: Filename for display
  - `get_display_path()`: Abbreviated path
  - `get_display_size()`: Human-readable size
  - `get_display_date()`: Formatted date

## State Management

### SearchState Enum
```python
class SearchState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"
```

### UI State Flow
1. **IDLE**: Ready for new search
2. **RUNNING**: Search in progress, UI responsive
3. **STOPPING**: User cancelled search
4. **COMPLETED**: Search finished successfully
5. **ERROR**: Search failed with error message

## Design Patterns

### 1. Model-View-Controller (MVC)
- **Models**: `ResultsModel`, `SearchResult`
- **Views**: PyQt6 widgets and dialogs
- **Controllers**: Main window and widget controllers

### 2. Signal-Slot Architecture
- **Decoupled communication** between components
- **Thread-safe** state updates
- **Event-driven** UI updates

### 3. Component-based Design
- **Reusable widgets** for common functionality
- **Modular architecture** for easy maintenance
- **Plugin integration** for extensibility

## Custom Features

### 1. Virtual Scrolling
- **Purpose**: Handle large result sets efficiently
- **Implementation**: Batch loading with 100-item chunks
- **Benefits**: Smooth scrolling, low memory usage

### 2. Custom Item Delegate
- **Purpose**: Custom result rendering with highlighting
- **Features**: Text highlighting, file icons, context menus
- **Performance**: Optimized painting for large lists

### 3. Drag and Drop Support
- **Search Input**: Directory and file dropping
- **Results View**: File dragging to external applications
- **Integration**: System clipboard and file manager integration

## Accessibility Features

### 1. Keyboard Navigation
- **Tab order**: Logical navigation between widgets
- **Shortcuts**: Common actions (Ctrl+F, Escape, Enter)
- **Menu access**: Alt+key for menu items

### 2. Visual Feedback
- **Focus indicators**: Clear focus states
- **Status updates**: Real-time progress and status
- **Error handling**: Clear error messages and recovery options
