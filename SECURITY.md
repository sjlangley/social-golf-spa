# Security Guidelines - Protecting Secrets

This document outlines security best practices for the Caringbah Social Golf Club application, specifically regarding secret management and preventing accidental exposure of credentials.

## Overview

This repository is configured to **prevent common secret files from being committed** to version control. The `.gitignore` file has been configured with comprehensive patterns to protect:

- Environment configuration files
- Google Cloud Platform service account keys
- Firebase configuration files
- SSL/TLS certificates and private keys
- SSH keys
- API keys and tokens
- Cloud provider credentials

## Protected File Patterns

### Environment Variables

**Ignored:**
- `.env` (and all `.env.*` variants)
- `.env.local`
- `.env.development.local`
- `.env.test.local`
- `.env.production.local`

**Allowed (templates only):**
- `.env.example`
- `.env.sample`
- `.env.template`

### Google Cloud & Firebase Credentials

**The following patterns are blocked from being committed:**

```
**/serviceAccountKey*.json
**/service-account*.json
**/gcp-key*.json
**/firebase-key*.json
**/*credentials*.json
**/*-credentials.json
application_default_credentials.json
google-credentials.json
gcp-credentials.json
firebase-config.json
firebase-adminsdk-*.json
firebaseServiceAccount.json
```

### Certificates and Keys

**All private key and certificate formats are blocked:**

```
*.pem
*.key
*.p12
*.pfx
*.cer
*.crt
*.der
*.jks
*.keystore
*.truststore
```

### SSH Keys

**All standard SSH key formats are blocked:**

```
id_rsa
id_rsa.pub
id_dsa
id_dsa.pub
id_ecdsa
id_ecdsa.pub
id_ed25519
id_ed25519.pub
```

### API Keys and Tokens

**Text files containing secrets are blocked:**

```
.apikey
.api-key
**/api-key*.txt
**/apikey*.txt
**/secret*.txt
**/token*.txt
access_token.txt
```

## Best Practices

### 1. Use Example Files for Configuration Templates

Instead of committing actual configuration:

```bash
# ❌ NEVER do this
git add .env
git commit -m "Add configuration"

# ✅ DO this instead
cp .env .env.example
# Remove all sensitive values from .env.example
git add .env.example
git commit -m "Add configuration template"
```

### 2. Use Environment Variables in Production

For production deployments on Cloud Run:

- Set environment variables through the Google Cloud Console or `gcloud` CLI
- Use Secret Manager for sensitive values
- **Never** hardcode secrets in source code
- **Never** commit `.env` files with production credentials

```bash
# Set environment variables for Cloud Run
gcloud run services update golf-api \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project \
  --set-secrets=DB_PASSWORD=db-password:latest
```

### 3. Use Google Cloud Secret Manager

For sensitive configuration that needs to be stored securely:

```bash
# Create a secret
echo -n "my-secret-value" | gcloud secrets create my-secret --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding my-secret \
  --member=serviceAccount:your-service-account@project.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Reference the secret in Cloud Run
gcloud run services update golf-api \
  --set-secrets=API_KEY=my-secret:latest
```

### 4. Local Development Setup

For local development, create a `.env` file (which is gitignored):

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your local values
# This file will NOT be committed
vim .env
```

### 5. Service Account Security

**Downloading Service Accounts:**

```bash
# Create and download a service account key
gcloud iam service-accounts keys create ~/service-account.json \
  --iam-account=your-service-account@project.iam.gserviceaccount.com

# Store it OUTSIDE the repository
# Add the path to your .env file
echo "GOOGLE_APPLICATION_CREDENTIALS=$HOME/service-account.json" >> .env
```

**Important:** Service account JSON files should:
- Be stored **outside** the repository directory
- Have restrictive file permissions (600)
- Be rotated regularly
- Be deleted when no longer needed

### 6. Pre-commit Checks

Before committing, always verify no secrets are staged:

```bash
# Check what files are staged
git status

# Review the actual content being committed
git diff --cached

# Check if any ignored files are being forced
git status --ignored
```

### 7. Accidental Secret Exposure

If you accidentally commit a secret:

1. **Rotate the secret immediately** (generate new credentials)
2. **Remove from Git history:**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   # This is complex - contact an admin for help
   ```
3. **Force push the cleaned history** (if repository is private)
4. **Report the incident** if the repository is public

### 8. Code Review Checklist

When reviewing pull requests, verify:

- [ ] No `.env` files are committed (except `.env.example`)
- [ ] No JSON files with "key", "secret", or "credentials" in the name
- [ ] No hardcoded API keys or passwords in source code
- [ ] No certificate or key files (`.pem`, `.key`, `.p12`, etc.)
- [ ] Configuration uses environment variables or Secret Manager
- [ ] Example files have placeholder values, not real secrets

## Monitoring and Detection

### GitHub Secret Scanning

GitHub automatically scans repositories for known secret patterns. If a secret is detected:

1. You'll receive an alert in the Security tab
2. The secret provider (e.g., Google Cloud) may be notified
3. **Immediate action required:** Rotate the exposed secret

### Regular Audits

Periodically check for accidentally committed secrets:

```bash
# Search for potential secrets in committed files
git grep -i "api.key\|password\|secret" \
  | grep -v ".gitignore\|SECURITY.md"

# Check for JSON files that might be credentials
git ls-files | grep -E "\.json$" \
  | grep -i "key\|secret\|credential\|firebase"
```

## Questions?

If you're unsure whether a file should be committed:

1. Check if it contains sensitive data (passwords, keys, tokens)
2. Check if it's matched by `.gitignore` patterns
3. When in doubt, **ask before committing**
4. Use `git check-ignore <filename>` to test if a file is ignored

## Resources

- [Google Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Remember:** It's easier to prevent secrets from being committed than to clean them up after the fact. Always use `.env.example` files and environment variables for configuration.
