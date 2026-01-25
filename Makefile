# OPTX - Online Privacy Tool eXtractor
# Terminal Colors
RED    := \033[0;31m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
CYAN   := \033[0;36m
NC     := \033[0m

.PHONY: all update clean help

# Default target: Fast Install + Start Server
all:
	@echo ""
	@echo "$(BLUE)OPTX:$(NC) Verifying environment..."
	@if [ ! -d "venv" ]; then \
		if python3 -m venv venv 2>err.log; then \
			echo "  $(GREEN)✓$(NC) Created virtual environment"; \
		else \
			echo "  $(RED)✗$(NC) Created virtual environment:"; \
			echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
			rm -f err.log; exit 1; \
		fi \
	fi
	@if ./venv/bin/pip install -q -U pip 2>err.log; then \
		echo "  $(GREEN)✓$(NC) pip"; \
	else \
		echo "  $(RED)✗$(NC) pip:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
		rm -f err.log; \
	fi
	@echo "$(YELLOW)  -> Installing packages from backend/requirements.txt:$(NC)"
	@while read -r line || [ -n "$$line" ]; do \
		if [ ! -z "$$line" ] && [ "$${line#\#}" = "$$line" ]; then \
			pkg=$$(echo $$line | cut -d'=' -f1 | cut -d'[' -f1); \
			if ./venv/bin/pip install -q $$line 2>err.log; then \
				echo "     $(GREEN)✓$(NC) $$pkg"; \
			else \
				echo "     $(RED)✗$(NC) $$pkg:"; \
				echo "       $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
			fi \
		fi \
	done < backend/requirements.txt
	@rm -f err.log
	@if ./venv/bin/playwright install chromium > /dev/null 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Playwright browsers"; \
	else \
		echo "  $(RED)✗$(NC) Playwright browsers:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
		rm -f err.log; \
	fi
	@echo "$(CYAN)  -> Checking for optional system dependencies:$(NC)"
	@if command -v ffmpeg >/dev/null 2>&1; then \
		echo "  $(GREEN)✓$(NC) ffmpeg (detected)"; \
	else \
		echo "  $(YELLOW)!$(NC) ffmpeg (not detected - required for audio CAPTCHA solving)"; \
	fi
	@echo "$(GREEN)SUCCESS:$(NC) Environment ready"
	@echo ""
	@echo "$(GREEN)OPTX:$(NC) Starting server..."
	@echo "  -> Open $(BLUE)http://localhost:3000$(NC) in your browser"
	@echo ""
	@./venv/bin/python backend/agent.py

# Update all dependencies
update:
	@echo ""
	@echo "$(BLUE)OPTX:$(NC) Updating dependencies..."
	@if [ ! -d "venv" ]; then \
		if python3 -m venv venv 2>err.log; then \
			echo "  $(GREEN)✓$(NC) Created virtual environment"; \
		else \
			echo "  $(RED)✗$(NC) Created virtual environment:"; \
			echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
			rm -f err.log; exit 1; \
		fi \
	fi
	@if ./venv/bin/pip install -q -U pip 2>err.log; then \
		echo "  $(GREEN)✓$(NC) pip"; \
	else \
		echo "  $(RED)✗$(NC) pip:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
		rm -f err.log; \
	fi
	@echo "$(YELLOW)  -> Updating packages from backend/requirements.txt:$(NC)"
	@while read -r line || [ -n "$$line" ]; do \
		if [ ! -z "$$line" ] && [ "$${line#\#}" = "$$line" ]; then \
			pkg=$$(echo $$line | cut -d'=' -f1 | cut -d'[' -f1); \
			if ./venv/bin/pip install -q -U $$line 2>err.log; then \
				echo "     $(GREEN)✓$(NC) $$pkg"; \
			else \
				echo "     $(RED)✗$(NC) $$pkg:"; \
				echo "       $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
			fi \
		fi \
	done < backend/requirements.txt
	@rm -f err.log
	@if ./venv/bin/playwright install chromium > /dev/null 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Playwright browsers"; \
	else \
		echo "  $(RED)✗$(NC) Playwright browsers:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
		rm -f err.log; \
	fi
	@echo ""
	@echo "$(GREEN)SUCCESS:$(NC) All dependencies updated"

# Deep clean: removes venv and all temporary caches
clean:
	@echo ""
	@echo "$(YELLOW)OPTX:$(NC) Deep cleaning...$(NC)"
	@echo "$(CYAN)  -> Removing virtual environment (venv/)...$(NC)"
	@rm -rf venv
	@echo "$(CYAN)  -> Clearing Python caches...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(CYAN)  -> Removing logs and temporary files...$(NC)"
	@rm -f *.log err.log
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(CYAN)  -> Clearing site-specific caches...$(NC)"
	@rm -rf .pytest_cache .coverage
	@echo ""
	@echo "$(GREEN)SUCCESS:$(NC) Full clean complete"

# Help
help:
	@echo ""
	@echo "$(BLUE)OPTX - Online Privacy Tool eXtractor$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(GREEN)Commands:$(NC)"
	@echo "  $(YELLOW)make$(NC)           Install/Verify dependencies + Start Server"
	@echo "  $(YELLOW)make update$(NC)    Update all library packages"
	@echo "  $(YELLOW)make clean$(NC)     Full reset (removes venv, caches, and logs)"
	@echo "  $(YELLOW)make help$(NC)      Show this list"
	@echo ""
	@echo "$(GREEN)API Keys & Usage:$(NC)"
	@echo "  $(CYAN)CEREBRAS_API_KEY$(NC)    Powers the ultra-fast $(CYAN)llama3.1-8b$(NC) reasoning chatbot"
	@echo "  $(CYAN)BROWSER_USE_API_KEY$(NC) The brain behind the AI agent that fills out opt-out forms"
	@echo "  $(CYAN)BROWSERLESS_API_KEY$(NC) High-performance browser engine for background automation"
	@echo ""
	@echo "Get keys: $(BLUE)https://cloud.cerebras.ai$(NC) | $(BLUE)https://cloud.browser-use.com$(NC) | $(BLUE)https://browserless.io$(NC)"
	@echo ""
