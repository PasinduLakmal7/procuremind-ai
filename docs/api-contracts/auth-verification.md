# Cross-Service Authentication & Permission Verification Contract

## 1. Stateless JWT Verification
To avoid making the Identity Service a single-point-of-failure or bottleneck for every internal request, microservices verify incoming JWT tokens statelessly.

### 2. Token Payload Specification
Signed with HMAC-SHA256 (or RSA-256):
```json
{
  "sub": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "officer@colombosteel.lk",
  "organization_id": "8bb1b827-047b-4ef9-bb6e-4f51543161c5",
  "roles": ["procurement_officer"],
  "token_type": "access",
  "exp": 1730000000,
  "iat": 1729996400,
  "jti": "d6fa0a41-a185-4b35-86f7-b8932fc446ae"
}
```

### 3. Verification Rules for Services
1. Extract Bearer token from `Authorization: Bearer <token>` header.
2. Verify token signature against `JWT_SECRET_KEY` and algorithm `JWT_ALGORITHM`.
3. Check `exp` (token expiration).
4. Extract `user_id` (`sub`), `organization_id`, and `roles`.
5. Enforce Organization Isolation: Ensure the resource being queried/mutated belongs to `organization_id`.
6. Enforce RBAC: Ensure `roles` contains required role for the endpoint (e.g. `procurement_manager`, `admin`).
7. Reject expired, tampered, or mismatched tokens with standard HTTP 401 Unauthorized or HTTP 403 Forbidden.

