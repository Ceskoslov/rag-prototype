# Task 27: Frontend ↔ Backend Integration + SSE Wiring

## Implementation Summary

**Date**: 2026-03-16  
**Task**: Wire frontend SSE hooks to real backend API endpoints with error handling and environment configuration

## Changes Made

### 1. Environment Configuration
**File**: `apps/frontend/.env.example` (NEW)
- Added `VITE_API_BASE_URL=/api/v1` - Backend API base URL
- Added `VITE_API_KEY=test-key` - API authentication key

### 2. Chat Hook - Backend Integration
**File**: `apps/frontend/src/hooks/useChat.ts`

**Key Changes**:
- **Switched from EventSource to fetch-based SSE streaming** (POST request support)
- Added `X-API-Key` header to all API requests
- Implemented proper SSE event parsing:
  - `token` → appends to current assistant message
  - `sources` → stores source documents in state
  - `trace` → updates agent trace panel data
  - `done` → stops loading state
- Added comprehensive error handling:
  - 401 → "Invalid API key" message
  - Network errors → user-friendly error display
  - Errors set in store for UI display
- Request body format matches backend schema:
  ```json
  {
    "message": "user query",
    "session_id": "uuid",
    "department": "it_support" | null
  }
  ```

### 3. Chat Store - Extended State Management
**File**: `apps/frontend/src/stores/chatStore.ts`

**Added**:
- `sources: SourceDocument[]` - Retrieved source documents from backend
- `error: string | null` - Error state for display
- `setSources()` - Method to update sources
- `setError()` - Method to update error state
- `SourceDocument` interface matching backend schema:
  ```typescript
  interface SourceDocument {
    title: string
    snippet: string
    department: string
  }
  ```

### 4. UI - Error Display
**File**: `apps/frontend/src/pages/ChatPage.tsx`

**Added**:
- Error banner display below message list
- Red-themed error UI with ARIA alert role
- Conditional rendering based on `error` state

### 5. Tests - Updated Mocking Strategy
**File**: `apps/frontend/src/hooks/__tests__/useChat.test.ts`

**Major Refactor**:
- Replaced `EventSource` mocking with `fetch` mocking
- Created `createSSEResponse()` helper to simulate SSE streams
- Updated all test cases to async/await pattern
- All 94 tests passing with new implementation

## SSE Event Format (Backend → Frontend)

Backend sends (from `apps/backend/app/services/chat.py`):
```
data: {"type": "heartbeat"}

data: {"type": "token", "content": "word"}

data: {"type": "sources", "data": [...]}

data: {"type": "trace", "data": {...}}

data: {"type": "done"}

```

Frontend parses:
1. Split stream by `\n`
2. Filter lines starting with `data: `
3. JSON.parse the payload
4. Switch on `type` field

## Error Handling

1. **API Unreachable**: Displays network error message to user
2. **401 Unauthorized**: Displays "Invalid API key" message
3. **SSE Connection Lost**: Error caught in try/catch, loading state disabled
4. **Exponential Backoff**: Already implemented in `useSSE.ts` (1s → 30s max delay)

## Environment Variables

**Production usage**:
```bash
VITE_API_BASE_URL=/api/v1  # Proxied through Nginx
VITE_API_KEY=your-production-key
```

**Local development**:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1  # Direct backend URL
VITE_API_KEY=test-key
```

## Verification

✅ TypeScript compilation: Clean (0 errors)  
✅ Tests: 94/94 passing  
✅ Department selector: Wired to API request body  
✅ Error states: Displayed in UI with red banner  
✅ API key: Sent in `X-API-Key` header  
✅ SSE parsing: Handles all backend event types  

## Manual QA (Deferred to Task F3)

Manual testing requires Docker services running:
```bash
docker compose up -d
# Navigate to http://localhost
# Select department → send message → verify streaming
```

This will be validated in Final Verification Wave (Task F3 with Playwright).

## Code Quality

- No console warnings during test run
- All existing tests updated to match new implementation
- Clean separation: useChat (business logic) vs chatStore (state)
- Error messages are user-friendly
- TypeScript types match backend schemas
