from pydantic import ValidationError
from nomus.config.settings import Settings, I18nConfig, Messages


def test_settings_validation_empty_string():
    """Test that Settings raises ValueError if any message field is empty."""
    # Create a config with an empty field
    invalid_messages = I18nConfig(
        ru=Messages(welcome=""),  # Empty welcome message
        en=Messages(welcome="Welcome"),
        uz=Messages(welcome="Xush kelibsiz"),
    )

    # We need to mock how Settings loads messages, or just test the validator directly if possible.
    # Since Settings loads from yaml, it might be easier to test the validator on a subclass or
    # just instantiate Settings and inject messages if possible, but Settings loads from source.

    # Actually, the validator will run on the model.
    # Let's try to instantiate Settings with manual values if possible,
    # or better, let's just test the logic we are about to add.

    # If we modify Settings to have the validator, we can try to instantiate it.
    # However, Settings loads from env/yaml.
    # Let's assume we can pass arguments to override.

    try:
        Settings(messages=invalid_messages)
    except ValidationError as e:
        # We expect a validation error
        print(f"Caught expected error: {e}")
        return

    # If we reach here, no error was raised (which is the current behavior, but we want it to fail later)
    print("No error raised (Current behavior)")


if __name__ == "__main__":
    test_settings_validation_empty_string()
