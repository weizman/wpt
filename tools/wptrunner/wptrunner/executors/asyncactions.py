from typing import List, Literal, Optional, TypedDict, Union


class WindowProxyProperties(TypedDict):
    context: str


class WindowProxyRemoteValue(TypedDict):
    """
    WebDriver BiDi browsing context descriptor.
    """
    type: Literal["window"]
    value: WindowProxyProperties


class BrowsingContextArgument(str):
    """Represent a browsing context argument passed from testdriver. It can be either a browsing context id, or a BiDi
    serialized window. In the latter case, the value is extracted from the serialized object."""

    def __new__(cls, context: Union[str, WindowProxyRemoteValue]):
        if isinstance(context, str):
            _context_id = context
        elif isinstance(context, dict) and "type" in context and context["type"] == "window":
            _context_id = context["value"]["context"]
        else:
            raise ValueError("Unexpected context type: %s" % context)
        return super(BrowsingContextArgument, cls).__new__(cls, _context_id)


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
            for browsing_context_argument in payload["contexts"]:
                contexts.append(BrowsingContextArgument(browsing_context_argument))
        return await self.protocol.bidi_events.subscribe(events, contexts)


async_actions = [BidiSessionSubscribeAction]
