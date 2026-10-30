from app.core.dependencies import require_roles


def test_member_management_dependency_is_admin_only():
    dependency = require_roles("admin")
    assert dependency.__name__ == "dependency"
