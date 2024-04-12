# Get the directory path of the script
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Change directory to the script directory
cd "$SCRIPT_DIR"

## Check so everything is in place before running the script

## Warn if not running on Ubuntu or Debian by checking the /etc/os-release file
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$NAME
else
  echo "Warning: /etc/os-release not found. This script has only been tested on Ubuntu and Debian."
  exit 1
fi

if [ "$OS" != "Ubuntu" ] && [ "$OS" != "Debian GNU/Linux" ]; then
  echo "Warning: This script has only been tested on Ubuntu and Debian."
  exit 1
fi

## Check so everything is installed
# GO
if ! [ -x "$(command -v go)" ]; then
  echo 'Error: go is not installed.' >&2
  exit 1
fi

# Python3
if ! [ -x "$(command -v python3)" ]; then
  echo 'Error: python3 is not installed.' >&2
  exit 1
fi

# Unzip
if ! [ -x "$(command -v unzip)" ]; then
  echo 'Error: unzip is not installed.' >&2
  exit 1
fi

# node
if ! [ -x "$(command -v node)" ]; then
  echo 'Error: node is not installed.' >&2
  exit 1
fi

## Build zDNS
# Pull all submodules
git submodule update --init --recursive

# Build zDNS
cd zdns

# Build the project
go build
cd ..

# Install the python dependencies
pip3 install -r requirements.txt
