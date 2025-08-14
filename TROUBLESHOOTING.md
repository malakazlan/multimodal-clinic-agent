# 🚨 Troubleshooting Guide

## Issue: Page Shows "Initialization" But Won't Load

If you're seeing the loading screen with "Initializing Healthcare AI" but the page never fully loads, follow these steps:

### 🔍 **Step 1: Check Browser Console**

1. **Open Developer Tools** (F12 or Right-click → Inspect)
2. **Go to Console tab**
3. **Look for any red error messages**
4. **Copy any error messages you see**

### 🔍 **Step 2: Use Debug Page**

1. **Navigate to:** `http://localhost:8000/debug.html`
2. **Check the system status**
3. **Look for missing elements**
4. **Test API connectivity**

### 🔍 **Step 3: Check API Endpoints**

Test these endpoints in your browser:

- **Health Check:** `http://localhost:8000/health`
- **Debug Info:** `http://localhost:8000/debug`
- **API Docs:** `http://localhost:8000/docs`

### 🔍 **Step 4: Common Issues & Solutions**

#### **Issue: Logging Errors (NameError: name 'json' is not defined)**
**Symptoms:** Server starts but shows logging errors in console
**Solutions:**
- This has been fixed in the latest code
- If you still see this error, restart the server
- Check that `utils/logger.py` has `import json` at the top

#### **Issue: JavaScript Errors**
**Symptoms:** Red errors in console
**Solutions:**
- Check if all HTML elements exist
- Verify JavaScript file is loading
- Clear browser cache and reload

#### **Issue: Missing Elements**
**Symptoms:** "Element not found" errors
**Solutions:**
- Ensure all required HTML elements exist
- Check element IDs match JavaScript
- Verify HTML structure is complete

#### **Issue: API Connection Problems**
**Symptoms:** Network errors or timeouts
**Solutions:**
- Check if server is running
- Verify port 8000 is accessible
- Check firewall settings

#### **Issue: CORS Problems**
**Symptoms:** Cross-origin errors
**Solutions:**
- Check CORS configuration in settings
- Verify allowed origins
- Test from correct domain

### 🔧 **Quick Fixes**

#### **Fix 1: Force Reload**
```bash
# Stop the server (Ctrl+C)
# Clear any cached files
rm -rf __pycache__/
# Restart the server
python main.py
```

#### **Fix 1.5: Fix Logging Error (if you see json error)**
```bash
# Stop the server (Ctrl+C)
# The logging error has been fixed in the code
# Just restart the server
python main.py
```

#### **Fix 2: Check Environment**
```bash
# Verify environment variables
python -c "
from config.settings import get_settings
settings = get_settings()
print(f'Environment: {settings.environment}')
print(f'Debug: {settings.debug}')
print(f'OpenAI Key: {bool(settings.openai_api_key)}')
"
```

#### **Fix 3: Browser Cache**
- **Chrome/Edge:** Ctrl+Shift+R (Hard Reload)
- **Firefox:** Ctrl+Shift+R (Hard Reload)
- **Safari:** Cmd+Option+R (Hard Reload)

### 🐛 **Debug Mode**

Enable debug mode by setting in your `.env` file:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### 📱 **Test Different Browsers**

Try accessing the app from:
- Chrome/Edge
- Firefox
- Safari
- Mobile browser

### 🔍 **Element Check**

Verify these elements exist in your HTML:
- `#app` - Main application container
- `#loadingScreen` - Loading screen
- `#recordBtn` - Record button
- `#chatMessages` - Chat messages area
- `#textInput` - Text input field

### 📋 **Checklist**

- [ ] Server is running on port 8000
- [ ] No JavaScript errors in console
- [ ] All required HTML elements exist
- [ ] API endpoints are accessible
- [ ] Environment variables are set
- [ ] Browser supports required features
- [ ] No network connectivity issues

### 🆘 **Still Having Issues?**

If the problem persists:

1. **Check the logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Run the test script:**
   ```bash
   python test_api.py
   ```

3. **Test logging system:**
   ```bash
   python test_logging.py
   ```

4. **Create a GitHub issue** with:
   - Error messages from console
   - Browser and OS information
   - Steps to reproduce
   - Screenshots if possible

### 🎯 **Expected Behavior**

After successful initialization, you should see:
1. Loading screen briefly appears
2. Main application interface loads
3. Welcome message in chat area
4. Microphone button becomes active
5. Status shows "Ready to listen"

### 🔄 **Reset Everything**

If all else fails:
```bash
# Stop server
# Clear all cached files
rm -rf __pycache__/ logs/* uploads/*

# Reinstall dependencies
pip install -r requirements.txt

# Restart server
python main.py
```

---

**Need more help?** Check the console logs and use the debug page at `/debug.html` to identify the specific issue.
