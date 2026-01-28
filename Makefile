.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running ruff check"
	@uv run ruff check pasteofshame
	@echo "🚀 Formatting check: Running ruff format"
	@uv run ruff format --check pasteofshame
	@echo "🚀 Static type checking: Running mypy"
	@uv run mypy pasteofshame
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry .

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules

.PHONY: benchmark
benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks"
	@uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-sort=mean

.PHONY: benchmark-save
benchmark-save: ## Save benchmark baseline
	@echo "💾 Saving benchmark baseline"
	@uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-save=baseline --benchmark-autosave

.PHONY: benchmark-compare
benchmark-compare: ## Compare current performance to baseline
	@echo "📊 Comparing performance to baseline"
	@uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-compare-fail=mean:10%

.PHONY: benchmark-verbose
benchmark-verbose: ## Run benchmarks with detailed output
	@echo "⚡ Running benchmarks with verbose output"
	@uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-verbose --benchmark-columns=min,max,mean,stddev,median,ops,rounds

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

# macOS App Targets
.PHONY: build-app-dev
build-app-dev: clean-app ## Build macOS application bundle in alias mode (development)
	@echo "🍎 Building macOS application bundle (development/alias mode)"
	@uv sync --group macos-app
	@mv pyproject.toml pyproject.toml.bak 2>/dev/null || true
	@uv run python setup.py py2app -A
	@mv pyproject.toml.bak pyproject.toml 2>/dev/null || true
	@echo "✅ App bundle created at dist/Paste of Shame.app (alias mode)"

.PHONY: build-app
build-app: clean-app ## Build standalone macOS application bundle
	@echo "🍎 Building standalone macOS application bundle"
	@uv sync --group macos-app
	@mv pyproject.toml pyproject.toml.bak 2>/dev/null || true
	@echo "⚙️  This may take a few minutes..."
	@uv run python setup.py py2app 2>&1 | tee build.log || (echo "❌ Build failed. Check build.log for details"; mv pyproject.toml.bak pyproject.toml 2>/dev/null; exit 1)
	@mv pyproject.toml.bak pyproject.toml 2>/dev/null || true
	@if [ -d "dist/Paste of Shame.app" ]; then \
		echo "✅ Standalone app created at dist/Paste of Shame.app"; \
		echo "📊 App size: $$(du -sh 'dist/Paste of Shame.app' | cut -f1)"; \
	else \
		echo "❌ Build failed. App not created."; \
		exit 1; \
	fi

.PHONY: clean-app
clean-app: ## Clean macOS app build artifacts
	@echo "🧹 Cleaning macOS app artifacts"
	@rm -rf build dist "Paste of Shame.dmg" build.log

.PHONY: build-dmg
build-dmg: build-app ## Build DMG installer for macOS app
	@echo "📦 Creating DMG installer"
	@./scripts/create_dmg.sh
	@echo "✅ DMG installer created at dist/Paste-of-Shame.dmg"

.PHONY: install-app
install-app: build-app ## Install macOS app to /Applications
	@echo "📲 Installing to /Applications"
	@cp -r "dist/Paste of Shame.app" /Applications/
	@echo "✅ Installed to /Applications/Paste of Shame.app"

.PHONY: install-launchagent
install-launchagent: ## Install LaunchAgent for auto-start on login
	@./scripts/install_autostart.sh

.PHONY: uninstall-launchagent
uninstall-launchagent: ## Uninstall LaunchAgent
	@./scripts/uninstall_autostart.sh

.PHONY: run-app
run-app: build-app ## Build and run the macOS app
	@echo "🚀 Running macOS app"
	@open "dist/Paste of Shame.app"

.PHONY: update-app
update-app: run-app
	@echo "🔄 Updating macOS app"
	@pkill -f "Paste of Shame.app" || true
	@echo "🔄 Relaunching macOS app"
	@open "dist/Paste of Shame.app"

.PHONY: logs
logs: ## Show app logs (tail -f)
	@echo "📋 Showing logs from /tmp/paste-of-shame.log"
	@echo "Press Ctrl+C to stop"
	@tail -f /tmp/paste-of-shame.log

.PHONY: logs-clear
logs-clear: ## Clear app logs
	@echo "🧹 Clearing logs"
	@rm -f /tmp/paste-of-shame.log
	@echo "✅ Logs cleared"

.PHONY: logs-show
logs-show: ## Show last 50 lines of app logs
	@echo "📋 Last 50 lines from /tmp/paste-of-shame.log"
	@tail -50 /tmp/paste-of-shame.log 2>/dev/null || echo "(No logs yet - start the app first)"

.DEFAULT_GOAL := build
