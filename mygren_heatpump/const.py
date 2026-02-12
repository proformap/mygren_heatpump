"""Constants for the Mygren Heat Pump integration."""

DOMAIN = "mygren_heatpump"

# Configuration
CONF_HOST = "host"

# Default values
DEFAULT_NAME = "Mygren Heat Pump"
DEFAULT_SCAN_INTERVAL = 30

# API endpoints
API_LOGIN = "/api/login"
API_TELEMETRY = "/api/telemetry"
API_DAEMONLOG = "/api/daemonlog"
API_RUNLOG = "/api/runlog"
API_RESOURCES = "/api/resources"

# TUV (Hot Water) endpoints
API_TUV = "/api/tuv"
API_TUV_SET = "/api/tuv/set"
API_TUV_ENABLED = "/api/tuv/enabled"
API_TUV_SCHEDULER_ENABLED = "/api/tuv/scheduler/enabled"
API_TUV_SCHEDULER = "/api/tuv/scheduler"

# Program endpoints
API_PROGRAM = "/api/program"
API_PROGRAM_PROGRAM = "/api/program/program"
API_PROGRAM_CURVE = "/api/program/curve"
API_PROGRAM_SHIFT = "/api/program/shift"
API_PROGRAM_MANUAL = "/api/program/manual"
API_PROGRAM_COMFORT = "/api/program/comfort"
API_PROGRAM_SCHEDULER_ENABLED = "/api/program/scheduler/enabled"
API_PROGRAM_SCHEDULER = "/api/program/scheduler"

# Heatpump endpoints
API_HEATPUMP = "/api/heatpump"
API_HEATPUMP_ENABLED = "/api/heatpump/enabled"
API_HEATPUMP_TARIFF = "/api/heatpump/tariff"
API_HEATPUMP_TARIFF_WATCH = "/api/heatpump/tariff/watch"

# Attribute names
ATTR_MAR_STATE = "mar_state"
ATTR_ONLINE = "online"
ATTR_COMPRESSOR = "compressor"
ATTR_HP_RUN = "hprun"
ATTR_HEATING = "heating"
ATTR_COOLING = "cooling"
ATTR_TUV_ENABLED = "tuv_enabled"
ATTR_TUV_SET = "tuv_set"
ATTR_HEAT = "heat"
ATTR_HEAT_DEST = "heat_dest"

# States
STATE_RUNNING = "running"
STATE_STOPPED = "stopped"
STATE_ERROR = "error"
