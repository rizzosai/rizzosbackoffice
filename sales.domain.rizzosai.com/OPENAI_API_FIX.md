# 🚨 URGENT: OpenAI API Key Fix Required

## Current Issue
The deployment logs show: `OpenAI API error: Error code: 401 - invalid_request_error`

This means the OpenAI API key is either:
- Not set in Render environment variables
- Invalid/expired key
- Incorrect key format

## ✅ How to Fix:

### Step 1: Get Valid OpenAI API Key
1. Go to https://platform.openai.com/account/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-proj-` or `sk-`)

### Step 2: Update Render Environment Variables  
1. Go to **Render Dashboard**: https://dashboard.render.com
2. Select your **rizzosbackoffice** service
3. Go to **Environment** tab
4. Set/Update: `OPENAI_API_KEY = sk-proj-[your-actual-key]`
5. Click **Save Changes**

### Step 3: Verify Fix
1. Render will automatically redeploy
2. Test Coey at: https://backoffice.rizzosai.com/coey
3. Send a message to verify it works

## 🔧 Current Environment Variables Needed:
```
SECRET_KEY=rizzos-secret-key-2024-secure
ADMIN_USERNAME=admin  
ADMIN_PASSWORD=rizzos2024
OPENAI_API_KEY=sk-proj-[your-actual-openai-key]
```

## 🎯 Expected Result:
After fixing, Coey should respond normally without 401 errors in the logs.

---
**Priority: CRITICAL** - Coey AI is currently non-functional for all users.