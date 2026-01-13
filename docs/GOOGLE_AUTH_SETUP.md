# Google Authentication Setup for google-docs-markdown

This guide walks you through setting up OAuth 2.0 credentials for `google-docs-markdown` on your personal computer.

> **Note:** If you're using a Google Workspace account, some of these steps may be simpler or unnecessary. This guide is optimized for personal Gmail accounts.

## Prerequisites

- A Google account (personal Gmail or Workspace)
- Access to Google Cloud Console
- The `gcloud` CLI installed on your machine
- A terminal/command line

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console – Create Project](https://console.cloud.google.com/projectcreate)
2. Enter a project name (e.g., `my-gdm-001`) and click **Create**
3. Wait for the project to be created (this may take a few moments)

## Step 2: Enable the Google Docs API

1. Go to [Google Cloud Console – Google Docs API](https://console.cloud.google.com/apis/api/docs.googleapis.com)
2. Click **Enable** to activate the Google Docs API for your project

## Step 3: Configure OAuth Consent Screen

1. Go to [Google Cloud Console – OAuth Consent Screen](https://console.cloud.google.com/auth/overview)
2. Click **Get started** under "OAuth Consent Screen"
3. On the "Project configuration" page:
   - **App name:** Enter a name for your app (e.g., `g-docs-markdown`)
   - **Support email:** Enter your email address
4. On the "Application type" page:
   - Choose **External** (or **Internal** if you're a Workspace user)
     - **External:** Recommended for personal Gmail accounts; you'll be added as a test user manually
     - **Internal:** For Workspace users only; no test user step required
5. Click **Create** (or **Save and Continue** as appropriate)

## Step 4: Create an OAuth 2.0 Desktop Client

1. Go to [Google Cloud Console – OAuth Clients](https://console.cloud.google.com/auth/clients)
2. Click **Create client**
3. Select **Desktop app** as the application type
4. Keep the default name (e.g., "Desktop client 1") or customize it
5. Click **Create**
6. When the "OAuth client created" dialog appears, click **Download JSON**
7. Save the downloaded file to a safe location on your machine:
   ```
   ~/.config/google-docs-markdown/client_id_file.json
   ```
   > If `~/.config/google-docs-markdown/` doesn't exist, create the directory first

## Step 5: Add Your Email as a Test User (External Apps Only)

> **Skip this step if you chose "Internal" in Step 3**

1. Go to [Google Cloud Console – OAuth Test Users](https://console.cloud.google.com/auth/audience)
2. Under "Test users," click **Add user**
3. Enter your email address
4. Click **Add**

## Step 6: Authenticate with gcloud

Run the following command in your terminal:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/sqlservice.login,openid \
  --client-id-file ~/.config/google-docs-markdown/client_id_file.json
```

> **Note:** Replace `~/.config/google-docs-markdown/client_id_file.json` with the actual path to your downloaded client secret file

## Step 7: Authorize in Your Browser

1. The command will open a browser window to the Google authentication page
2. Click your email address to select your account
3. You'll see a warning: **"Google hasn't verified this app"**
   - This is expected because your app is still in testing mode
   - Click **Continue** to proceed (do not click "Back to safety")
4. Grant permissions to the app:
   - Click **Select all** to grant all requested permissions
   - Click **Continue**
5. The browser tab will close and your terminal will display:
   ```
   Credentials saved to file: [/Users/<username>/.config/gcloud/application_default_credentials.json]
   ```

## Step 8: Verify Your Setup

Run a test command to confirm everything is working:

```bash
gdm download "https://docs.google.com/document/d/YOUR_DOCUMENT_ID/edit"
```

Replace `YOUR_DOCUMENT_ID` with an actual Google Docs document ID. If successful, the document will be downloaded as Markdown.

## Troubleshooting

### "This app is blocked" error

If you receive an error saying "This app is blocked," you may be missing the `--client-id-file` flag. Ensure you're using the full command from Step 6 with the correct path to your `client_id_file.json` file.

### Credentials file not found

If you get an error about missing credentials, double-check that:
- The `client_id_file.json` file was downloaded and saved to the correct location
- The path in the command matches the file's actual location

### Test user not added

If you chose "External" in Step 3 and are still seeing permission errors, verify that you added your email as a test user in Step 5.

## What's Next?

Your credentials are now stored locally in `~/.config/gcloud/application_default_credentials.json` and will be used automatically by the `google-docs-markdown` tool. You don't need to authenticate again unless you revoke the credentials or your token expires.

To revoke access at any time, go to [Google Account Connected Apps & Sites](https://myaccount.google.com/permissions) and remove the `g-docs-markdown` app.
