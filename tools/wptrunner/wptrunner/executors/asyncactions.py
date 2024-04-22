# mypy: allow-untyped-defs
from typing import List, Literal, Optional, TypedDict, Union


class WindowProxyProperties(TypedDict):
    context: str


class WindowProxyRemoteValue(TypedDict):
    """
    WebDriver BiDi browsing context descriptor.
    """
    type: Literal["window"]
    value: WindowProxyProperties


BrowsingContextArgument = Union[str, WindowProxyRemoteValue]


def get_browsing_context_id(context: BrowsingContextArgument) -> str:
    """
    Extracts browsing context id from the argument. The argument can be either a string or a BiDi serialized window
    proxy.
    :param context: Browsing context argument.
    :return: Browsing context id.
    """
    if isinstance(context, str):
        return context
    elif isinstance(context, dict) and "type" in context and context["type"] == "window":
        return context["value"]["context"]
    else:
        raise ValueError("Unexpected context type: %s" % context)


class BidiSessionSubscribeAction:
    name = "bidi.session.subscribe"

    class Payload(TypedDict):
        """
        Payload for the "bidi.session.subscribe" action.
        events: List of event names to subscribe to.
        contexts: Optional list of browsing contexts to subscribe to. Each context can be either a BiDi serialized
        value, or a string. The latter is considered as a browsing context id.
        """
        events: List[str]
        contexts: Optional[List[BrowsingContextArgument]]

    def __init__(self, logger, protocol):
        self.logger = logger
        self.protocol = protocol

    async def __call__(self, payload: Payload):
        events = payload["events"]
        contexts = None
        if payload["contexts"] is not None:
            contexts = []
            for context_argument in payload["contexts"]:
                contexts.append(get_browsing_context_id(context_argument))
        return await self.protocol.bidi_events.subscribe(events, contexts)


async_actions = [BidiSessionSubscribeAction]
