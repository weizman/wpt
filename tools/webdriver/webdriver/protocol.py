# mypy: allow-untyped-defs

import json

import webdriver


"""WebDriver wire protocol codecs."""


class Encoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs.pop("session")
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, (list, tuple)):
            return [self.default(x) for x in obj]
        elif isinstance(obj, webdriver.WebElement):
            return {webdriver.WebElement.identifier: obj.id}
        elif isinstance(obj, webdriver.WebFrame):
            return {webdriver.WebFrame.identifier: obj.id}
        elif isinstance(obj, webdriver.ShadowRoot):
            return {webdriver.ShadowRoot.identifier: obj.id}
        elif isinstance(obj, webdriver.WebWindow):
            return {webdriver.WebWindow.identifier: obj.id}
        return super().default(obj)

    def _wrap_bidi_values(self, obj):
        """
        For backward compatibility, we need to encode WebDriver BiDi values in WebDriver Classic format. In order to do
        that, we need to check if any of the dict to be encoded is a WebDriver BiDi object and encode it accordingly.
        """
        if isinstance(obj, dict):
            if 'type' in obj and obj['type'] == 'node' and "sharedId" in obj:
                # Backwards compatibility for WebDriver BiDi serialization.
                return {webdriver.WebElement.identifier: obj["sharedId"]}
            else:
                # Recursively encode nested dictionaries.
                return {key: self._wrap_bidi_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            # Recursively encode elements in the list
            return [self._wrap_bidi_values(item) for item in obj]
        elif isinstance(obj, tuple):
            # Recursively encode elements in the tuple
            return tuple(self._wrap_bidi_values(item) for item in obj)
        elif isinstance(obj, set):
            # Recursively encode elements in the set
            return {self._wrap_bidi_values(item) for item in obj}
        else:
            # Return other types as is
            return obj

    def encode(self, obj):
        return super().encode(self._wrap_bidi_values(obj))


class Decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        super().__init__(
            object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, payload):
        if isinstance(payload, (list, tuple)):
            return [self.object_hook(x) for x in payload]
        elif isinstance(payload, dict) and webdriver.WebElement.identifier in payload:
            return webdriver.WebElement.from_json(payload, self.session)
        elif isinstance(payload, dict) and webdriver.WebFrame.identifier in payload:
            return webdriver.WebFrame.from_json(payload, self.session)
        elif isinstance(payload, dict) and webdriver.ShadowRoot.identifier in payload:
            return webdriver.ShadowRoot.from_json(payload, self.session)
        elif isinstance(payload, dict) and webdriver.WebWindow.identifier in payload:
            return webdriver.WebWindow.from_json(payload, self.session)
        elif isinstance(payload, dict):
            return {k: self.object_hook(v) for k, v in payload.items()}
        return payload
