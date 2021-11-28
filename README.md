# AA-Statistics

AA-Statistics for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth).

Periodically gather and update statistics for use by other modules

Currently used by

- AA-DiscordBot
- AA-SmartGroups

Currently offers

- [ZKillboard](https://zkillboard.com/) Stats

## Setup

1. `pip install git+https://github.com/pvyParts/aa-statistics.git`
2. add `'aastatistics',` to INSTALLED_APPS in your `local.py`
3. migrate database and restart auth

```bash
python manage.py migrate
python manage.py collectstatic
```

4. Add the following lines to your local.py

```python
## Settings for AA-Statistics
MEMBER_ALLIANCES = [111, 222, 333] # Alliances you care about statistics for
## Periodic Tasks for AA-Statistics
CELERYBEAT_SCHEDULE['aastatistics.run_stat_model_update'] = {
    'task': 'aastatistics.run_stat_model_update',
    'schedule': crontab(minute=0, hour=0,)
}
```

## Issues

Please remember to report any AA-Statistics related issues using the issues on **this** repository.

## Contribute

All contributions are welcome, but please if you create a PR for functionality or bugfix, do not mix in unrelated formatting changes along with it.
