# Setting Up PostgreSQL Database on DigitalOcean

Follow these steps to add persistent data storage to your bot on DigitalOcean:

## Step 1: Add PostgreSQL Database

1. Go to your DigitalOcean App dashboard
2. Click on your app (nightshade bot)
3. Click **"Create"** → **"Database"**
4. Select **"PostgreSQL"**
5. Choose **"Dev Database"** (it's FREE!)
6. Click **"Create and Attach"**

## Step 2: Verify DATABASE_URL

1. Go to **Settings** → **App-Level Environment Variables**
2. You should see `DATABASE_URL` automatically created by DigitalOcean
3. If not, you'll need to add it manually (copy from the database component)

## Step 3: Redeploy Your App

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

## Troubleshooting

### "Database not available" error
- Make sure `DATABASE_URL` environment variable is set
- Check that the database is attached to your app
- Verify the database is running (green status)

### "Failed to connect to database"
- Check the database URL format (should start with `postgresql://`)
- DigitalOcean sometimes uses `postgres://` which needs to be changed to `postgresql://`
- The bot handles this automatically, but check logs for connection errors

### Stats still resetting
- Make sure you redeployed after adding the database
- Check logs to confirm database connection succeeded
- Run `/myprofile` and play a game to verify stats are saving

## Migration from Old Bot

If you had data on a previous deployment, you won't be able to recover it since the old deployment used ephemeral storage. The database ensures this doesn't happen again!

All new data will persist forever in the PostgreSQL database.
