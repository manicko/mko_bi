TASK: Fix env var mapping for nested models in pydantic-settings

FILE: src/mko_bi/config.py

GOAL: Ensure environment variables like DATABASE__HOST properly override YAML values with correct priority.

IMPLEMENT:

* Investigate why DATABASE__HOST env var doesn't map to database.host while JWT__SECRET_KEY works.
* Check pydantic-settings version and behavior for nested models.
* Possibly adjust settings_customise_sources ordering or env var naming.
* Ensure priority: env vars > Docker secrets > .env > YAML > defaults.

LOGIC:

1. pydantic-settings 2.14.0 with nested models and env_nested_delimiter="__".
2. JWT__SECRET_KEY works, DATABASE__HOST doesn't.
3. Maybe the issue is that DATABASE__HOST is being mapped to a nested model that has default values from YAML.
4. Could be that the env var is being read but then overwritten by YAML source because of ordering.
5. Use test: tests/test_config.py::TestSettingsPriority::test_env_overrides_yaml

DONE:

* [ ] Env var DATABASE__HOST overrides YAML value.
* [ ] Env var JWT__SECRET_KEY loads correctly.
* [ ] Priority order verified.
* [ ] All config tests pass (241 passed, 0 failed).

---

### Additional context:

**Failing tests:**
- `tests/test_config.py::TestSettingsPriority::test_env_overrides_yaml`
- `tests/test_config.py::TestSettingsPriority::test_env_overrides_dotenv`

**Observation:**
Setting `DATABASE__HOST=env-host` doesn't override YAML value `database.host: localhost`.
But `JWT__SECRET_KEY=env-secret` correctly sets `jwt.secret_key`.

**Hypotheses:**
1. pydantic-settings handles nested model fields differently when YAML source is present.
2. The `settings_customise_sources` ordering might be incorrect.
3. Possibly the `database` nested model has `password` and `secret_key` fields that are `None` by default, affecting mapping.

**Steps to investigate:**
1. Create minimal reproduction script with pydantic-settings nested models.
2. Check if the issue is specific to `database` nested model vs `jwt` nested model.
3. Try different `settings_customise_sources` orderings.
4. Check if `env_nested_delimiter` works with custom sources.
5. Consider upgrading/downgrading pydantic-settings.
