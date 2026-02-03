DOMAIN = "paperlesspaper_push"

CONF_API_KEY = "api_key"
CONF_PAPER_ID = "paper_id"
CONF_BASE_URL = "base_url"
CONF_INPUT_DIR = "input_dir"
CONF_PUBLISH_DIR = "publish_dir"
CONF_TIMEOUT = "timeout"
CONF_MAX_ATTEMPTS = "max_attempts"
CONF_PUBLISH = "publish"

DEFAULT_BASE_URL = "https://api.memo.wirewire.de/v1"
DEFAULT_INPUT_DIR = "/media/picture-frames/paperlesspaper"
DEFAULT_PUBLISH_DIR = "/config/www/picture-frames/paperlesspaper"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_ATTEMPTS = 4
DEFAULT_PUBLISH = True

STORE_VERSION = 1
STORE_KEY_STATE = f"{DOMAIN}_state"
STORE_KEY_RECENT = f"{DOMAIN}_recent"

ATTR_CURRENT_FILENAME = "current_filename"
ATTR_LAST_RESULT = "last_result"
ATTR_LAST_HTTP_STATUS = "last_http_status"
ATTR_LAST_ERROR = "last_error"

STATE_SUCCESS = "success"
STATE_FAILED = "failed"

SERVICE_UPLOAD_RANDOM = "upload_random"
SERVICE_RESET_RECENT = "reset_recent"
SERVICE_FIELD_FORCE_FILE = "force_file"
SERVICE_FIELD_DRY_RUN = "dry_run"
SERVICE_FIELD_PUBLISH = "publish"
