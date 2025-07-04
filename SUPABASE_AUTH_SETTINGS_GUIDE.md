# Step-by-Step Guide: Supabase Authentication Settings

## 🎯 How to Find Authentication Settings

### Step 1: Access Your Project
1. Go to: https://supabase.com/dashboard
2. Sign in to your Supabase account
3. Click on your project: **VisionSeal** or the project with ID `fycatruiawynbzuafdsx`

### Step 2: Navigate to Authentication
1. In the left sidebar, look for: **🔐 Authentication**
2. Click on **Authentication**
3. You'll see a submenu appear

### Step 3: Find Settings
In the Authentication submenu, you should see:
- **Users** (list of users)
- **Policies** (RLS policies)
- **Templates** (email templates)
- **Settings** ← **CLICK HERE**

### Step 4: Locate User Signup Settings
1. Click on **Settings**
2. Scroll down to find section: **"User Signups"**
3. Look for these toggles:
   - ☑️ **"Enable new user signups"** (should be enabled)
   - ☑️ **"Confirm new users"** ← **DISABLE THIS**
   - ☐ **"Auto-confirm users"** ← **ENABLE THIS**

## 🔍 Alternative Navigation Paths

### If you can't find "Authentication":
Try these alternatives:
1. Look for **"Auth"** instead of "Authentication"
2. Look for a **🔐 lock icon** in the sidebar
3. Check if it's under **"Settings"** → **"Auth"**

### If the sidebar is collapsed:
1. Look for a hamburger menu (≡) to expand it
2. Or look for small icons on the left side

### Direct URL Method:
Try going directly to:
```
https://supabase.com/dashboard/project/fycatruiawynbzuafdsx/auth/users
```
Then look for "Settings" tab at the top.

## 📱 Mobile/Small Screen:
If you're on mobile or small screen:
1. Look for a menu button (☰)
2. Authentication might be in a collapsible menu
3. Try switching to desktop view

## 🎯 What to Change

Once you find the settings:

**DISABLE:**
- ☐ Confirm new users

**ENABLE:**  
- ☑️ Auto-confirm users
- ☑️ Enable new user signups

## 🚨 Can't Find It? Alternative Solution

If you still can't find the settings, I can create a workaround that handles email confirmation in the code. Let me know and I'll implement that solution instead.

## 📞 Need Help?

If you're still having trouble:
1. Take a screenshot of your Supabase dashboard
2. Let me know what you see in the left sidebar
3. I'll provide more specific guidance based on your interface

The authentication system is working - we just need this one setting change! 🔧✨