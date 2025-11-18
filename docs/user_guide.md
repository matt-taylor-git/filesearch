# File Search User Guide

Welcome to the File Search application! This guide will help you get the most out of your file searching experience.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Search](#basic-search)
3. [Working with Results](#working-with-results)
4. [Opening Files](#opening-files)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Security Features](#security-features)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Launching the Application

```bash
# From source
python -m filesearch

# Or if installed via pip
filesearch
```

### Main Interface

The File Search interface consists of:

- **Search Bar**: Enter your search terms and file patterns
- **Directory Selector**: Choose which directories to search
- **Results Panel**: Displays found files and folders
- **Status Bar**: Shows search progress and file opening status
- **Sort Controls**: Options to organize your results

## Basic Search

### Performing a Search

1. **Select Directory**: Use the directory selector to choose where to search
2. **Enter Search Terms**: Type your query in the search bar
3. **Choose File Types** (optional): Filter by specific file extensions
4. **Start Search**: Press Enter or click the search button

### Search Patterns

- **Text Search**: Find files containing specific text
- **File Name Patterns**: Use wildcards like `*.txt` or `document?.pdf`
- **Combined Search**: `*.py AND "import os"`

### Search Filters

- **File Types**: Documents, images, videos, code files
- **Size Range**: Small (<1MB), Medium (1-10MB), Large (>10MB)
- **Date Range**: Today, This Week, This Month, Custom Range

## Working with Results

### Understanding the Results Panel

Results are displayed in a list showing:

- **File Name**: The name of the found file
- **Path**: Directory location
- **Size**: File size
- **Modified Date**: Last modification time
- **File Type**: Document, image, video, etc.

### Sorting Results

Use the sort controls to organize results by:

- **Name**: Alphabetical order (A-Z or Z-A)
- **Size**: Smallest to largest or vice versa
- **Date Modified**: Newest or oldest first
- **Type**: Group by file type

### Selecting Results

- **Single Click**: Select a file to highlight it
- **Double Click**: Open the file (see [Opening Files](#opening-files))
- **Arrow Keys**: Navigate up and down through results
- **Ctrl+Click**: Select multiple files (when supported)

## Opening Files

### Double-Click to Open

The fastest way to open files is by double-clicking them:

1. **Find your file** in the results list
2. **Double-click** the file name
3. **File opens** in your system's default application

**Example**: Double-clicking a `.txt` file opens it in your default text editor, while a `.jpg` opens in your image viewer.

### Keyboard Activation (Enter Key)

You can also open files using your keyboard:

1. **Select a file** by single-clicking or using arrow keys
2. **Press Enter** to open it
3. **File opens** just like double-clicking

### Supported File Types

File Search supports opening virtually any file type:

| File Type | Extensions | Opens With |
|-----------|------------|-------------|
| **Documents** | .txt, .pdf, .docx, .odt | Default document viewer/editor |
| **Images** | .jpg, .png, .gif, .bmp | Default image viewer |
| **Videos** | .mp4, .avi, .mkv, .mov | Default media player |
| **Audio** | .mp3, .wav, .flac, .m4a | Default music player |
| **Code** | .py, .js, .html, .css | Default code editor |
| **Archives** | .zip, .rar, .7z, .tar | Archive manager |
| **Folders** | Directories | File manager |

### Platform-Specific Behavior

File Search uses your operating system's native file opening:

- **Windows**: Uses `os.startfile()` - opens files with associated applications
- **macOS**: Uses `open` command - respects default app associations
- **Linux**: Uses `xdg-open` - follows desktop environment defaults
- **Cross-platform**: Qt fallback ensures compatibility

### Visual Feedback

When you open a file, you'll see:

- **Highlight Flash**: The selected item briefly highlights
- **Cursor Change**: Mouse cursor becomes a pointer hand on hover
- **Status Messages**: 
  - "Opening: filename.txt..." (while opening)
  - "Opened: filename.txt" (success)
  - "Failed to open: [error]" (if there's a problem)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Enter** | Open selected file |
| **↑/↓** | Navigate up/down through results |
| **Home** | Jump to first result |
| **End** | Jump to last result |
| **Ctrl+F** | Focus search bar |
| **Escape** | Clear search/stop current search |
| **F5** | Refresh search |

## Security Features

### Executable File Warnings

For your safety, File Search warns you before opening executable files:

**Executable Files Include:**
- Windows: `.exe`, `.bat`, `.cmd`, `.msi`
- macOS/Linux: `.sh`, `.command`, `.app`
- Scripts: `.py`, `.js`, `.vbs` (when executable)

**Warning Dialog:**
```
⚠️ This is an executable file. Open anyway?

[ ] Always allow .exe files
[Open] [Cancel]
```

**Options:**
- **Open**: Open the file after confirming
- **Cancel**: Cancel the operation
- **Always allow**: Remember your choice for this file type

### Error Handling

File Search handles common errors gracefully:

| Error | Message | Solution |
|-------|---------|----------|
| **File Not Found** | "File no longer exists: [path]" | File was moved or deleted |
| **No Default App** | "No application associated with this file type" | Install appropriate software |
| **Permission Denied** | "Permission denied: [path]" | Check file permissions |
| **Network Issues** | "Network location unavailable" | Check network connection |

**Fallback Option**: When errors occur, File Search offers to "Open Containing Folder" so you can manually locate the file.

## Advanced Features

### Search During Search

File Search prevents accidental file opening during active searches:

- **During Search**: Double-click is disabled
- **Search Complete**: Double-click automatically re-enabled
- **Visual Indicator**: Status shows "Searching..." during operation

### Most Recently Used (MRU)

File Search remembers your recently opened files:

- **Storage**: Last 10 opened files saved in preferences
- **Quick Access**: MRU list available in settings
- **Privacy**: MRU can be cleared in preferences

### Configuration Options

Access settings to customize:

- **Security**: Enable/disable executable warnings
- **File Associations**: Choose default applications
- **Search Behavior**: Default directories, file type filters
- **UI Preferences**: Theme, font sizes, layout options

## Troubleshooting

### Files Won't Open

**Problem**: Double-clicking doesn't open files

**Solutions**:
1. **Check File Association**: Ensure your system has a default app for the file type
2. **Verify File Exists**: The file may have been moved or deleted
3. **Check Permissions**: Ensure you have read access to the file
4. **Try Manual Open**: Right-click and "Open Containing Folder"

### Slow File Opening

**Problem**: Files take a long time to open

**Solutions**:
1. **Large Files**: Very large files may take longer to load
2. **Network Drives**: Network locations may be slower
3. **System Resources**: Check if your system is busy
4. **Application Issues**: Try restarting File Search

### Security Warnings

**Problem**: Getting warnings for safe files

**Solutions**:
1. **Check Extension**: Verify the file extension is correct
2. **File Properties**: Some files may be marked as executable
3. **Whitelist**: Use "Always allow" option for trusted file types
4. **Settings**: Adjust security preferences in settings

### Performance Issues

**Problem**: Search is slow or unresponsive

**Solutions**:
1. **Narrow Search**: Use specific file patterns
2. **Exclude Large Files**: Filter by file size
3. **Check Directory**: Avoid searching system directories
4. **System Resources**: Close other applications

## Getting Help

### Additional Resources

- **📖 Documentation**: Check the `docs/` folder for technical documentation
- **🐛 Issue Tracker**: Report bugs at [GitHub Issues](https://github.com/filesearch/filesearch/issues)
- **💬 Discussions**: Ask questions at [GitHub Discussions](https://github.com/filesearch/filesearch/discussions)

### Keyboard Navigation Tips

- **Tab Navigation**: Use Tab to move between interface elements
- **Quick Search**: Start typing to focus the search bar
- **Result Navigation**: Use arrow keys to browse results without mouse
- **Context Menus**: Right-click results for additional options (when available)

---

**Happy File Searching!** 🚀

If you need help with specific features or encounter issues, don't hesitate to reach out through our support channels.