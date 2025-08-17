# Quay.io Registry Secrets Setup

This document explains how to configure repository secrets for dual registry pushing to both GitHub Container Registry (GHCR) and Quay.io.

## Required Secrets

To enable container mirroring to Quay.io, the following repository secrets must be configured:

### 1. QUAY_USERNAME
- **Name:** `QUAY_USERNAME`
- **Value:** `karlssoc`
- **Description:** Username for the Quay.io registry account

### 2. QUAY_PASSWORD
- **Name:** `QUAY_PASSWORD`
- **Value:** [Quay.io password or application token]
- **Description:** Authentication token for Quay.io registry access

## Setup Instructions

### Step 1: Access Repository Settings
1. Navigate to the repository: https://github.com/karlssoc/ck-pybis-toolkit
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

### Step 2: Add Quay.io Username
1. Click **New repository secret**
2. Enter name: `QUAY_USERNAME`
3. Enter value: `karlssoc`
4. Click **Add secret**

### Step 3: Add Quay.io Password/Token
1. Click **New repository secret**
2. Enter name: `QUAY_PASSWORD`
3. Enter your Quay.io password or application token
4. Click **Add secret**

## Security Recommendations

### Use Application Tokens (Recommended)
Instead of using your account password, create a dedicated application token:

1. Log in to [quay.io](https://quay.io)
2. Go to **Account Settings** → **Robot Accounts**
3. Create a new robot account with push permissions to `karlssoc/ck-pybis-toolkit`
4. Use the robot account token as `QUAY_PASSWORD`

### Minimal Permissions
The token should have only the necessary permissions:
- **Repository:** `karlssoc/ck-pybis-toolkit`
- **Permissions:** Write (push containers)

## Verification

After configuring the secrets, you can verify the setup by:

1. **Triggering a workflow:** Push to the `main` branch or create a release
2. **Check workflow logs:** Ensure both registry logins succeed
3. **Verify containers:** Check that containers appear in both registries:
   - GHCR: `ghcr.io/karlssoc/ck-pybis-toolkit:latest`
   - Quay.io: `quay.io/karlssoc/ck-pybis-toolkit:latest`

## Troubleshooting

### Authentication Failures
- **Check secret names:** Ensure `QUAY_USERNAME` and `QUAY_PASSWORD` are exact
- **Verify credentials:** Test login locally with `docker login quay.io`
- **Token expiration:** Check if application tokens need renewal

### Repository Permissions
- **Repository exists:** Ensure `quay.io/karlssoc/ck-pybis-toolkit` repository exists
- **Write access:** Verify the account has push permissions
- **Public repository:** Ensure the repository is configured as public for deployment access

### Workflow Failures
- **Missing secrets:** Check that both secrets are properly configured
- **Registry connectivity:** Verify GitHub Actions can reach quay.io
- **Schema compatibility:** Ensure `provenance: false` is set in the workflow

## Expected Results

Once properly configured, the workflow will:

1. **Login to both registries** during container builds
2. **Generate tags for both** GHCR and Quay.io automatically
3. **Push containers** to both registries simultaneously
4. **Maintain compatibility** with Singularity v3.7 via Docker V2 Schema 2

This enables seamless container distribution across both GitHub Container Registry and Quay.io for consistent deployment workflows.