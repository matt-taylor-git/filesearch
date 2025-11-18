# File Search

A cross-platform file search application with extensible plugin architecture, built with Python and PyQt6.

## Features

- **Fast File Searching**: Efficient search across directories with real-time results
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Extensible Architecture**: Plugin system for custom search providers and result processors
- **Modern UI**: Clean, intuitive interface built with PyQt6
- **Advanced Filtering**: Filter by file type, size, date, and content patterns
- **Result Management**: Sort, filter, and export search results
- **Performance Optimized**: Multi-threaded search with progress indication

## Installation

### Prerequisites

- Python 3.9 or higher
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/filesearch/filesearch.git
cd filesearch
```

2. Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies (optional):
```bash
pip install -r requirements-dev.txt
```

## Usage

### Running the Application

```bash
# From source
python -m filesearch

# Or if installed via pip
filesearch
```

### Command Line Options

```bash
python -m filesearch [options]

Options:
  --help     Show help message
  --version  Show version information
```

## Development

### Project Structure

```
filesearch/
├── src/filesearch/          # Main package
│   ├── core/               # Core functionality
│   ├── plugins/            # Plugin architecture
│   └── ui/                 # User interface components
├── tests/                  # Test suite
├── config/                 # Configuration files
├── docs/                   # Documentation
├── pyproject.toml         # Project configuration
├── requirements.txt       # Runtime dependencies
└── requirements-dev.txt   # Development dependencies
```

### Code Quality

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **pytest** for testing
- **pre-commit** hooks for automated checks

Run checks manually:
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Run tests
pytest

# Run with coverage
pytest --cov=filesearch --cov-report=html
```

### Testing

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m ui

# Run with verbose output
pytest -v
```

## Architecture

### Core Components

- **Search Engine**: Multi-threaded file search with pattern matching
- **Plugin System**: Extensible architecture for custom functionality
- **UI Framework**: PyQt6-based interface with model-view architecture
- **Configuration**: TOML-based configuration with environment overrides
- **Logging**: Structured logging with rotation and compression

### Technology Stack

- **Python 3.9+**: Modern Python with type hints
- **PyQt6**: Cross-platform GUI framework
- **loguru**: Structured logging
- **platformdirs**: Platform-specific directory paths
- **pytest**: Testing framework with pytest-qt for UI testing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

1. Install pre-commit hooks:
```bash
pre-commit install
```

2. Run tests before committing:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/filesearch/filesearch/issues)
- 💬 [Discussions](https://github.com/filesearch/filesearch/discussions)

## Roadmap

See our [project roadmap](docs/roadmap.md) for upcoming features and improvements.
