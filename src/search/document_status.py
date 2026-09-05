# INFRASTRUCTURE
import logging

from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.network.types import ResourceType

logger = logging.getLogger(__name__)


# FUNCTIONS

# Arm a Network.responseReceived listener on tab's own main frame BEFORE the first navigation, so
# it also catches that first navigation's own response — collects the ORDERED chain of main-frame
# document response statuses into the returned list. A FACT, never a verdict; nothing here decides
# "blocked"/"challenge-solved" — same principle as src/scraper/chromium_scrape.py's
# document_status_chain, via CDP's Network domain directly instead of Playwright's page.on. Setup
# failure degrades to an empty list (never raises) so a CDP hiccup here cannot turn an ordinary
# search into a new engine error.
async def start_document_status_capture(tab) -> list[int]:
    status_chain: list[int] = []
    main_frame_id = tab._target_id

    def _on_response(event: dict) -> None:
        params = event.get("params") or {}
        if params.get("type") != ResourceType.DOCUMENT:
            return
        if params.get("frameId") != main_frame_id:
            return
        status = (params.get("response") or {}).get("status")
        if status is not None:
            status_chain.append(status)

    try:
        await tab.enable_network_events()
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, _on_response)
    except Exception as e:
        logger.warning("document-status capture setup failed (degrading to no observation): %s", e)
    return status_chain


# Merge the network-observed status facts into a diagnosis snapshot, after the fact — http_status
# is the LAST main-frame document response, not the first hop of a redirect chain; None (never a
# fabricated default) when no document response was observed at all
def attach_document_status(diag: dict, status_chain: list[int]) -> dict:
    return {
        **diag,
        "document_status_chain": list(status_chain),
        "http_status": status_chain[-1] if status_chain else None,
    }
