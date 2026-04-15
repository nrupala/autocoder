# Contributing to AutoCoder

Thank you for your interest in contributing to AutoCoder!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/autocoder.git
cd autocoder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements.txt[dev]
```

## Code Style

We use:
- **Ruff** for linting
- **Black** for formatting
- **MyPy** for type checking

```bash
# Run linting
ruff check .

# Run formatting
black .

# Run type checking
mypy core/ models/ memory/ security/ tools/
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_core.py -v
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with conventional commits
6. Push to your fork
7. Submit a Pull Request

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Welcome newcomers
