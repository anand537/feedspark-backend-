# Authentication Audit TODO

## Plan (Pending User Confirmation)

### File 1: `app/models/user.py`
- Add `status` column: `afg_db.Column(afg_db.String(20), default='pending')`

### File 2: `app/decorators.py`
- Fix `role_required` to look up `User` from JWT identity and check `user_type`

### File 3: `app/routes/auth.py`
1. Fix `register_user`:
   - Accept `name` and `user_type`
   - Use `set_password()` instead of broken `password_hash=...`
   - Set `email_verified=False`, `status='pending'`
   - Generate email verification token via model method
   - Return `verification_token` + `user_id`
2. Add `/check-email` endpoint
3. Add `/verify-email/<token>` endpoint
4. Fix `login_user`:
   - Change `user.is_verified` → `user.email_verified`
   - Add `status == 'approved'` validation
   - Include `user_type` in JWT additional_claims
5. Fix `get_current_user`: return `email_verified` instead of `is_verified`
6. Keep existing OTP routes for backward compatibility

### File 4: `app/api/users.py`
- Add `/api/users/pending` (GET, super-admin)
- Add `/api/users/<id>/approve` (POST, super-admin)
- Add `/api/users/<id>/reject` (POST, super-admin)

### File 5: `tests/test_api_endpoints.py`
- Update test setup to set `email_verified=True` and `status='approved'` on test users
- Update `test_auth_register_and_login` to include admin approval step

## Followup Steps
- Run `python -m pytest tests/test_api_endpoints.py`

