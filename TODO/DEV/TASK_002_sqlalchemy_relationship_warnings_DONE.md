---
## TASK: Fix SQLAlchemy relationship warnings
---

### PROBLEM

SQLAlchemy relationship warnings appear during test execution:

```
SAWarning: relationship 'Dashboard.users' will copy column dashboards.id to column dashboard_access.dashboard_id, which conflicts with relationship(s): 'DashboardAccess.dashboard'
SAWarning: relationship 'User.dashboards' will copy column users.id to column dashboard_access.user_id, which conflicts with relationship(s): 'DashboardAccess.user'
```

### ROOT CAUSE

The relationships in the database models have overlapping foreign key constraints that need to be properly configured with `back_populates` or `overlaps` parameter.

### FILES TO CHECK

- `src/mkobi/db/models/dashboard.py`
- `src/mkobi/db/models/user.py`
- `src/mkobi/db/models/access.py`

### SOLUTION

Add `overlaps` parameter to the relationships or configure `back_populates` properly:

```python
# In Dashboard model
users = relationship(
    "User", secondary="dashboard_access", overlaps="dashboard,dashboard_access"
)

# In User model
dashboards = relationship(
    "Dashboard", secondary="dashboard_access", overlaps="user,dashboard_access"
)

# In DashboardAccess model
dashboard = relationship("Dashboard", overlaps="users,dashboard_access")
user = relationship("User", overlaps="dashboards,dashboard_access")
```

### VERIFICATION

1. Run `uv run pytest tests/` 
2. Check that SAWarning messages are no longer present

### PRIORITY

Low - warnings don't break functionality

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Warnings resolved

---
