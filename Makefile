.PHONY: test test-backend test-e2e test-unit serve

# Run all Python backend tests
test-backend:
	python -m pytest tests/ -v

# Run frontend unit tests (Vitest)
test-unit:
	npm test

# Run Playwright E2E tests (requires server on :8000)
test-e2e:
	npx playwright test --config playwright.config.js

# Run all tests
test: test-backend test-unit test-e2e

# Start development server
serve:
	python -m uvicorn backend.app.main:app --reload
