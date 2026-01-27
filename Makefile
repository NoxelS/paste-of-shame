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
	@echo "🚀 Installing LaunchAgent"
	@mkdir -p ~/Library/LaunchAgents
	@cp resources/com.pasteofshame.app.plist ~/Library/LaunchAgents/
	@launchctl load ~/Library/LaunchAgents/com.pasteofshame.app.plist
	@echo "✅ LaunchAgent installed and loaded"

.PHONY: uninstall-launchagent
uninstall-launchagent: ## Uninstall LaunchAgent
	@echo "🗑️  Uninstalling LaunchAgent"
	@launchctl unload ~/Library/LaunchAgents/com.pasteofshame.app.plist 2>/dev/null || true
	@rm -f ~/Library/LaunchAgents/com.pasteofshame.app.plist
	@echo "✅ LaunchAgent uninstalled"

.PHONY: run-app
run-app: build-app ## Build and run the macOS app
	@echo "🚀 Running macOS app"
	@open "dist/Paste of Shame.app"

.DEFAULT_GOAL := build
