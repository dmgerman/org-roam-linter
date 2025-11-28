# Code Quality and Style

- **Production Quality**: Code must be production-ready with proper error handling, logging, and robustness
- **Functional Programming Style**: Avoid mutation as much as possible
  - Use immutable data structures where practical
  - Prefer function composition and pure functions
  - Minimize side effects (I/O operations should be isolated at boundaries)
  - Use `map()`, `filter()`, `reduce()` and comprehensions instead of loops with mutations
  - Return new data structures instead of modifying existing ones
  - Use type hints throughout for clarity and runtime checking support
- **Function Design**: Keep functions small and focused
  - Each function should have a single, clear responsibility
  - Aim for functions that fit on a single screen
  - Break down complex logic into smaller, composable functions
- **Code Organization**: Structure functions to be composable and testable
- **DRY Principle**: No code duplication
  - Extract repeated logic into reusable functions
  - Use helper functions to eliminate duplication across features
- **Error Handling**: Validate inputs and handle edge cases gracefully
- **Logging**: Include appropriate logging for debugging (especially with `--debug` flag)
