# AG Channels

Synchronises lists of people with Telegram channels; i.e. adds all people
with a phone number to the specified channel.

Doesn't yet work; we still need to decide what channels to use and sync to. For
now, this only contains the function required to actually add people.

Author: Martijn Brehm (mattermost: `@martijn_amsterdam`)
Date: 10/20/2020

## Pre-requisites

Python 3

## Installation

Clone or download repository onto local computer.

```bash
git clone https://github.com/xrnl/rebel_management_utilities.git
```


Install necessary dependencies.

```bash
pip3 install -r requirements.txt
```

Requires following info in `.env` file.

```
TELEGRAM_ID=<..>              // (string): the id of the telegram api app created for this script.
TELEGRAM_HASH=<..>            // (string): the hash of the telegram api app id for this script.
TELEGRAM_USERNAME=<..>        // (string): telegram username of the telegram account used to run the script.
ACTION_NETWORK_API_KEY=<..>   // (string): api key for action network.
```

## Usage

```bash
python3 ./sync_telegram_channels.py
```
