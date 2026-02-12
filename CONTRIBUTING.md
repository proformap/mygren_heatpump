# Contributing to Mygren Heat Pump Integration

Thank you for your interest in contributing to the Mygren Heat Pump integration for Home Assistant!

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Home Assistant version**
- **Integration version**
- **Heat pump model and firmware version**
- **Relevant log entries** (enable debug logging)
- **Configuration details** (remove sensitive information)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other ways to solve the problem
- **Additional context**: Screenshots, mockups, etc.

### API Documentation

If you have access to additional Mygren API documentation or endpoints not currently documented, please share:

- API endpoint details
- Request/response examples
- Any undocumented features
- Testing results

This is particularly valuable for:
- Setting HVAC mode (heat/cool/off)
- Enabling/disabling hot water heating
- Confirming heating temperature control endpoint
- Any additional control endpoints

## Development Setup

### Prerequisites

- Python 3.11 or newer
- Home Assistant development environment
- Access to a Mygren heat pump (or test data)

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/mygren_heatpump.git
   cd mygren_heatpump
   ```

3. Set up Home Assistant development environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install Home Assistant
   pip install homeassistant

   # Install development dependencies
   pip install pytest pytest-homeassistant-custom-component
   ```

4. Link integration to Home Assistant:
   ```bash
   # Create custom_components directory in your HA config
   mkdir -p /path/to/homeassistant/config/custom_components
   
   # Symlink the integration
   ln -s /path/to/mygren_heatpump /path/to/homeassistant/config/custom_components/
   ```

### Code Style

Please follow these guidelines:

- **PEP 8**: Follow Python style guide
- **Black**: Use Black code formatter with default settings
- **Type hints**: Include type hints for function parameters and returns
- **Docstrings**: Document classes and functions
- **Comments**: Add comments for complex logic

Example:
```python
async def async_set_temperature(self, **kwargs: Any) -> None:
    """Set new target temperature.
    
    Args:
        kwargs: Keyword arguments containing temperature value
    """
    temperature = kwargs.get("temperature")
    if temperature is None:
        return
    
    # Your implementation here
```

### Testing

Before submitting a pull request:

1. **Test locally**: Verify the integration works on your system
2. **Check logs**: Ensure no errors in Home Assistant logs
3. **Test all features**: Verify existing features still work
4. **Document changes**: Update README if adding features

### Pull Request Process

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow code style guidelines
   - Add comments and docstrings
   - Update documentation

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```
   
   Use clear commit messages:
   - `Add:` New features
   - `Fix:` Bug fixes
   - `Update:` Updates to existing features
   - `Docs:` Documentation changes

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**:
   - Provide clear description of changes
   - Reference any related issues
   - Include testing details
   - Add screenshots if UI changes

## Code Structure

```
mygren_heatpump/
├── __init__.py           # Integration setup and coordinator
├── manifest.json         # Integration metadata
├── const.py             # Constants and configuration
├── mygren_api.py        # API client
├── config_flow.py       # UI configuration flow
├── sensor.py            # Sensor entities
├── binary_sensor.py     # Binary sensor entities
├── climate.py           # Climate entity
├── water_heater.py      # Water heater entity
└── translations/        # Localization files
    └── en.json
```

## Adding New Features

### Adding a New Sensor

1. Add sensor description to `sensor.py`:
   ```python
   MygrenSensorEntityDescription(
       key="new_sensor_key",
       name="New Sensor Name",
       native_unit_of_measurement="unit",
       device_class=SensorDeviceClass.TYPE,
       state_class=SensorStateClass.MEASUREMENT,
       value_fn=lambda data: data.get("api_field_name"),
   )
   ```

2. Document in README.md

### Adding API Endpoint

1. Add endpoint constant to `const.py`:
   ```python
   API_NEW_ENDPOINT = "/api/new_endpoint"
   ```

2. Add method to `mygren_api.py`:
   ```python
   def get_new_data(self) -> dict[str, Any]:
       """Get new data from API."""
       return self._make_request("GET", API_NEW_ENDPOINT)
   ```

3. Use in entities or coordinator

## Translation

To add a new language:

1. Create translation file:
   ```
   translations/sk.json  # Slovak example
   ```

2. Copy structure from `en.json`

3. Translate all strings

## Documentation

When adding features, update:

- **README.md**: Main documentation
- **INSTALLATION.md**: Installation instructions
- **EXAMPLES.md**: Usage examples
- **Code comments**: Inline documentation

## Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and features
- **Pull Requests**: Use GitHub PRs for contributions

## Additional Notes

### API Testing

If testing new API endpoints:

```python
# Test script example
import requests

host = "http://your-heat-pump-ip"
token = "your-token"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

response = requests.get(f"{host}/api/endpoint", headers=headers)
print(response.json())
```

### Debug Logging

Enable debug logging in Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.mygren_heatpump: debug
```

### Known Limitations

Current limitations requiring contribution:

1. HVAC mode control endpoint unknown
2. Hot water enable/disable endpoint unknown
3. Heating temperature control endpoint assumed
4. Schedule management not implemented
5. Advanced settings not exposed

## Questions?

If you have questions:

1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Create a new issue

## Code of Conduct

Be respectful and constructive in all interactions. We're all here to improve this integration together.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
