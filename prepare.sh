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

# Ask if User want to install all dependencies

echo "Do you want to install all dependencies for the project? This will invoke sudo."
read -r -p "Continue? [y/N] " response

# if yes
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  echo "Installing all dependencies"
  # Install all dependencies
  sudo apt install ca-certificates fonts-liberation \
    libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
    libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 \
    libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
    libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
    libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils -y
fi

echo "Done"