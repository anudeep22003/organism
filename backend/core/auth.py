from loguru import logger

logger = logger.bind(name=__name__)

acceptable_tokens = {"6qjEjJ0tbM374wq1eDg2AnVAawhbHvdCNFLQu4qqC5g"}


def verify_session_token(session_token: str) -> bool:
    logger.debug("Verifying session token", session_token=session_token)
    if session_token not in acceptable_tokens:
        logger.debug("Invalid session token", session_token=session_token)
        return False
    return True
