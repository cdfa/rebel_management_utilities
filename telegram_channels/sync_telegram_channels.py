from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.errors.rpcerrorlist import FloodWaitError

from convert_phone import convert_phone_number

from time import sleep
import logging
from dotenv import load_dotenv
import os
import os.path


async def sync_telegram_channel(client, people, channel, invitation):
    """
        Syncs the list of people with the members of the specified telegram
        channels; skips people without a 'phone_number' field.

        Send people a Telegram message with a link to join the channel. Adds
        the first 200 people automatically (Telegram only allows
        automatic addition up till 200...).

        Params:
        - client : Telegram client object.
        - people (list) : list of dicts containing contact info. Assumes dicts
                          containg a 'phone_number' and 'given_name' entry.
        - channel (string) : id of the telegram channel/group.
        - invitation (string) : invitation message send to new people.
    """
    p_in_channel = [p.phone for p in await client.get_participants(channel) if p.phone]

    for p in people:
        p["phone_number"] = convert_phone_number(p["phone_number"])

        # Add to channel.
        if p["phone_number"] not in p_in_channel:
            try:
                await client.send_message(p["phone_number"], invitation)
                if len(p_in_channel) < 200:
                    await add_user(client, p, channel)
                logging.info("Successfully invited person: {}".format(p))

            except IndexError as e: # Person doesn't have Telegram.
                logging.warning("Person has no telegram account: {}".format(p))
            except Exception as e: # Other errors.
                logging.warning("Couldn't add person: {}".format(p))


async def add_user(client, person, channel):
    """
        Adds the specified user to the specified telegram channel. Assumes
        person has a 'phone_number' field.

        No error handling; if the person doesn't have telegram, this gives
        an exception.

        Params:
        - client : Telegram client object.
        - person (dict) : a dictionary of describing a person.
        - channel (string) : id of the telegram channel/group.
    """
    # Add user to contact. This allows us to add them to the channel
    contact = InputPhoneContact(
        client_id=0,
        phone=person["phone_number"],
        first_name=person["given_name"],
        last_name="xr_automatic_telegram_script"
    )

    # Wait for 60 second time constraints on adding contact.
    while True:
        try:
            result = await client(ImportContactsRequest([contact]))
            break
        except FloodWaitError as e:
            print("Flood error - waiting: {}".format(e))
            sleep(60)

    # Add them to the correct channel.
    await client(InviteToChannelRequest(channel, [result.users[0]]))


def main():
    # Set up telegram client and launch sync loop.
    load_dotenv()
    client = TelegramClient(os.getenv("TELEGRAM_USERNAME"), os.getenv("TELEGRAM_ID"), os.getenv("TELEGRAM_HASH"))
    client.start()

    # TODO: sync the required telegram groups/channels.


if __name__ == '__main__':
    main()
