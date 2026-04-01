# Contributing to ShuttleKit

Thanks for your interest in contributing to ShuttleKit! We welcome contributions of all kinds — bug reports, feature requests, documentation improvements, and code changes.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ShuttleKit.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit with clear messages: `git commit -m "Add feature: description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd web
npm install
```

### Running Tests

From the **`api/`** directory (where `pytest.ini` lives):

```bash
cd api
pytest tests/api/ -v
```

## Code Style

- Python: Follow PEP 8 guidelines
- TypeScript/React: Follow the existing code style (Prettier/ESLint configs)
- Write clear, descriptive variable and function names
- Add comments for complex logic
- Keep functions focused and modular

## Pull Request Guidelines

- Keep PRs focused on a single feature or bug fix
- Include tests for new functionality
- Update documentation (README, docstrings) as needed
- Ensure all tests pass before submitting
- Provide a clear description of what your PR does and why

## Reporting Issues

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Node version)
- Relevant logs or error messages

## Feature Requests

We're open to new ideas! When suggesting features:

- Explain the use case and problem it solves
- Describe the proposed solution
- Consider backward compatibility
- Be open to discussion and alternative approaches

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project and community
- Help others learn and grow

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.

Thank you for contributing! 🚌
