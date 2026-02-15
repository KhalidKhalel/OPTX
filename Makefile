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
	@if [ ! -f ".env" ]; then \
		echo "$(CYAN)OPTX:$(NC) First time setup"; \
		echo ""; \
		echo "  You need a Browserless API key (free)."; \
		echo "  Get yours at: $(BLUE)https://www.browserless.io$(NC)"; \
		echo ""; \
		printf "  Enter your API key: "; \
		read api_key; \
		echo "# Browserless - Browser Automation" > .env; \
		echo "BROWSERLESS_API_KEY=$$api_key" >> .env; \
		echo "BROWSERLESS_WS_URL=wss://production-sfo.browserless.io" >> .env; \
		echo ""; \
		echo "  $(GREEN)✓$(NC) Created .env file"; \
	fi
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
	@echo "$(GREEN)SUCCESS:$(NC) Environment ready"
	@echo ""
	@echo "$(GREEN)OPTX:$(NC) Starting server..."
	@echo "  -> Open $(BLUE)http://localhost:3000$(NC) in your browser"
	@echo ""
	@cd backend && ../venv/bin/python agent.py

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
	@echo "$(YELLOW)OPTX:$(NC) Deep cleaning..."
	@echo "$(YELLOW)  -> Clearing temporary files...$(NC)"
	@if rm -rf venv 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed virtual environment"; \
	else \
		echo "  $(RED)✗$(NC) Removed virtual environment:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if rm -f .env 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed .env file"; \
	else \
		echo "  $(RED)✗$(NC) Removed .env file:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if rm -rf backend/__pycache__ 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed backend pycache"; \
	else \
		echo "  $(RED)✗$(NC) Removed backend pycache:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if find . -type d -name "__pycache__" -exec rm -rf {} + 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed deep pycache"; \
	else \
		echo "  $(RED)✗$(NC) Removed deep pycache:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if find . -name "*.pyc" -delete 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed .pyc files"; \
	else \
		echo "  $(RED)✗$(NC) Removed .pyc files:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if find . -name ".DS_Store" -delete 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed .DS_Store files"; \
	else \
		echo "  $(RED)✗$(NC) Removed .DS_Store files:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@if find . -name "*.log" -delete 2>err.log; then \
		echo "  $(GREEN)✓$(NC) Removed log files"; \
	else \
		echo "  $(RED)✗$(NC) Removed log files:"; \
		echo "    $(RED)Error: $$(cat err.log | tr '\n' ' ')$(NC)"; \
	fi
	@rm -f err.log
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
	@echo "  $(YELLOW)make clean$(NC)     Full reset (removes venv and all caches)"
	@echo "  $(YELLOW)make help$(NC)      Show this list"
	@echo ""
	@echo "$(GREEN)API Key:$(NC)"
	@echo "  $(CYAN)BROWSERLESS_API_KEY$(NC) Cloud browser for stealth automation and captcha solving"
	@echo ""
	@echo "Get your free key: $(BLUE)https://browserless.io$(NC)"
	@echo ""
