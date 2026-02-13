"""Constants for the Mygren Heat Pump integration."""

DOMAIN = "mygren_heatpump"

# Configuration keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_VERIFY_SSL = "verify_ssl"

# Default values
DEFAULT_NAME = "Mygren Heat Pump"
DEFAULT_SCAN_INTERVAL = 30

# API endpoints (relative to /api)
API_LOGIN = "/api/login"
API_TELEMETRY = "/api/telemetry"
API_RESOURCES = "/api/resources"
API_DAEMONLOG = "/api/daemonlog"
API_RUNLOG = "/api/runlog"

# TUV (Hot Water) endpoints
API_TUV = "/api/tuv"
API_TUV_SET = "/api/tuv/set"
API_TUV_ENABLED = "/api/tuv/enabled"
API_TUV_SCHEDULER_ENABLED = "/api/tuv/scheduler/enabled"

# Program endpoints
API_PROGRAM = "/api/program"
API_PROGRAM_PROGRAM = "/api/program/program"
API_PROGRAM_CURVE = "/api/program/curve"
API_PROGRAM_SHIFT = "/api/program/shift"
API_PROGRAM_MANUAL = "/api/program/manual"
API_PROGRAM_COMFORT = "/api/program/comfort"
API_PROGRAM_SCHEDULER_ENABLED = "/api/program/scheduler/enabled"

# Heatpump endpoints
API_HEATPUMP = "/api/heatpump"
API_HEATPUMP_ENABLED = "/api/heatpump/enabled"
API_HEATPUMP_TARIFF = "/api/heatpump/tariff"
API_HEATPUMP_TARIFF_WATCH = "/api/heatpump/tariff/watch"
