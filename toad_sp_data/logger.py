import logging


# define VERBOSE only if it wasn't defined before importing this file
verbose = None
if "VERBOSE" in globals():
    verbose = globals().get("VERBOSE")  # pragma: no cover
VERBOSE = verbose


# configure logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def log_info(msg):  # pragma: no cover
    logger.info(msg)


def log_error(msg):  # pragma: no cover
    logger.error(msg)


def log_info_verbose(msg):  # pragma: no cover
    if VERBOSE:
        logger.info(msg)


def log_error_verbose(msg):  # pragma: no cover
    if VERBOSE:
        logger.error(msg)
