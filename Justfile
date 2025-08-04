set shell := ["bash", "-cu"]
set positional-arguments

default:
	@echo "Usage: just <command> [<args>]"
	@echo "Available commands:"
	@echo "  k <project> [task] - Run the Justfile in 'k8s/<project>'"

k *args:
    cd "k8s/$1" && shift && just "$@"
