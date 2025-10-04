.PHONY: seed help

help:
	@echo "Use the root Makefile one directory up: make -C .. <target>"
	@echo "Common: make -C .. seed | make -C .. deploy | make -C .. status"

# Convenience forwarder so you can run `make seed` from backend/
seed:
	@$(MAKE) -C .. seed
