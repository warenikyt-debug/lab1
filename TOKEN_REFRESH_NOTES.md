# Token Refresh Behavior

## Current Implementation Status

✅ **Backend** (fully working):
- POST /api/auth/refresh returns 200 with new tokens
- Returns: `{ "access_token": "...", "refresh_token": "..." }`
- One-time use: Second refresh with same token returns 401 error ✅

✅ **Frontend** (partially implemented):
- Automatic refresh on 401 error when loading /me
- Manual refresh via text input in profile page
- ❌ **MISSING**: Automatic refresh before token expires

## Problem Analysis

The current code ONLY refreshes:
1. When /api/auth/me returns 401 (token already expired)
2. When user manually pastes token and clicks button

**What's missing**:
- Proactive refresh BEFORE token expires
- Auto-refresh on application startup if token is near expiry

## Token Structure (JWT)

The JWT contains:
```json
{
  "user_id": 1,
  "type": "access",
  "token_id": "09c6c4e7-...",
  "exp": 1774796576.3,  // Unix timestamp
  "iat": 1774792976.3
}
```

**Token lifetime**: 60 minutes for access, 7 days for refresh

## Solution

To auto-refresh tokens, frontend needs to:

1. Decode JWT to extract `exp` (expiration time)
2. Calculate time until expiration
3. If expiration < 5 minutes, call `/api/auth/refresh` BEFORE it expires
4. Save new tokens to localStorage
5. Continue operation

## Example Implementation

```javascript
function getTokenExpiration() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    // Decode JWT (no verification needed, we trust our own token)
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    try {
        const payload = JSON.parse(atob(parts[1]));
        return payload.exp * 1000; // Convert to milliseconds
    } catch (e) {
        return null;
    }
}

async function autoRefreshIfNeeded() {
    const expTime = getTokenExpiration();
    if (!expTime) return;
    
    const now = Date.now();
    const timeUntilExpiry = expTime - now;
    const refreshBefore = 5 * 60 * 1000; // 5 minutes
    
    if (timeUntilExpiry < refreshBefore) {
        console.log('Token expires soon, refreshing...');
        await refreshToken();
    }
}

// Call on app startup
document.addEventListener('DOMContentLoaded', autoRefreshIfNeeded);
```

## Current Test Results

All tests PASS with curl:
```bash
1. Login → get tokens ✅
2. First refresh → new tokens ✅
3. Second refresh with old token → 401 error (correct) ✅
4. Refresh with new token → new tokens ✅
```

The backend is working perfectly. The issue is frontend integration.

## Recommendations

1. **Keep current behavior**: Works fine for active users
2. **Add auto-refresh**: For better UX, implement proactive token refresh
3. **Consider**: Adding token expiration warning to UI

