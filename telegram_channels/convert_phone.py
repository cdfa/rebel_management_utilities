import phonenumbers


def convert_phone_number(phonenumber):
    """
        Parses a phonenumber and returns it in E.164 format (i.e. +31 6 ..).
        When a provided phonenumber has no country code (i.e. 06 12 ..) the
        Dutch country code is assumed and added.

        Params:
        - phonenumber (string) : the given phonenumber. Can be any format.

        Returns:
        - on succes: (string): the phonenumber in E.164 format.
        - on failure: None.
    """
    # Country code was provided and detected.
    try:
        return phonenumbers.format_number(
                phonenumbers.parse(phonenumber),
                phonenumbers.PhoneNumberFormat.E164
        )
    # No country code provided - assume the number is Dutch.
    except phonenumbers.phonenumberutil.NumberParseException as e:
        try:
            return phonenumbers.format_number(
                    phonenumbers.parse(phonenumber, "NL"),
                    phonenumbers.PhoneNumberFormat.E164
            )
        # Invalid number
        except Exception as e:
            return None
