# Setting Up Database with Supabase (FREE!)

Follow these steps to add persistent data storage to your bot using Supabase's free PostgreSQL database:

## Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up with GitHub (recommended) or email
4. **It's completely FREE** - no credit card required!

## Step 2: Create a New Project

1. Click **"New Project"**
2. Fill in:
   - **Name:** nightshade-bot (or whatever you want)
   - **Database Password:** Create a strong password (save this!)
   - **Region:** Choose closest to your DigitalOcean region
   - **Pricing Plan:** FREE (default)
3. Click **"Create new project"**
4. Wait 2-3 minutes for setup to complete

## Step 3: Get Your Database URL

1. In your Supabase project dashboard, click **"Settings"** (gear icon)
2. Click **"Database"** in the left sidebar
3. Scroll down to **"Connection string"**
4. Select **"URI"** tab
5. Copy the connection string that looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
6. **Replace `[YOUR-PASSWORD]`** with the password you created in Step 2

## Step 4: Add Database URL to DigitalOcean

1. Go to your DigitalOcean App dashboard
2. Click on your app (nightshade bot)
3. Go to **Settings** → **App-Level Environment Variables**
4. Click **"Edit"**
5. Add a new variable:
   - **Key:** `DATABASE_URL`
   - **Value:** Paste your Supabase connection string
6. Click **"Save"**

## Step 5: Redeploy Your App

1. Click **"Actions"** → **"Force Rebuild and Deploy"**
2. Wait for deployment to complete
3. Check the logs - you should see:
   ```
   ✅ Connected to PostgreSQL database
   ✅ PostgreSQL tables created/verified
   ```

## Step 4: Test It Out!

1. Play some games (Tic Tac Toe, Connect Four, etc.)
2. Win a few rounds
3. Use `/myprofile` to see your stats
4. Restart your app on DigitalOcean
5. Use `/myprofile` again - your stats should still be there! ✅

## Step 6: Verify It's Working (Optional but Recommended)

1. In Supabase, go to **"Table Editor"** in the left sidebar
2. After your bot runs for the first time, you should see these tables:
   - `user_stats` - Stores game wins and userphone stats
   - `warnings` - Stores warning data
   - `bot_config` - Stores bot configuration

## Troubleshooting

### "Database not available" error
- Make sure `DATABASE_URL` environment variable is set in DigitalOcean
- Verify you replaced `[YOUR-PASSWORD]` with your actual password
- Check Supabase project is active (green status)

### "Failed to connect to database"
- Verify the connection string starts with `postgresql://` (not `postgres://`)
- Make sure you're using the **Connection Pooler** URL (port 6543) not the Direct URL if you get timeout errors
- In Supabase: Settings → Database → Connection Pooler → URI

### Stats still resetting
- Make sure you redeployed after adding `DATABASE_URL`
- Check DigitalOcean logs to confirm database connection succeeded
- Run `/myprofile` and play a game to verify stats are saving
- Check Supabase Table Editor to see if data appears

### Connection timeout
If you get connection timeouts, use Supabase's **Connection Pooler** instead:
1. In Supabase: Settings → Database
2. Look for **"Connection Pooler"** section
3. Use the **Transaction mode** URL (port 6543)
4. Update `DATABASE_URL` in DigitalOcean with the pooler URL

## Why Supabase?

✅ **FREE Forever** - Up to 500MB database (plenty for Discord bots!)  
✅ **No Credit Card Required**  
✅ **Built-in Dashboard** - View your data easily  
✅ **Automatic Backups**  
✅ **Fast & Reliable**  
✅ **PostgreSQL** - Same database as big companies use  

## Supabase Free Tier Limits

- **Storage:** 500 MB (your bot will use ~1-10 MB)
- **Bandwidth:** 5 GB/month (Discord bot uses very little)
- **API Requests:** Unlimited
- Perfect for Discord bots! 🎉
