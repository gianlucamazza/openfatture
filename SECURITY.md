# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: info@gianlucamazza.it

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Best Practices

### For Users

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use strong passwords for PEC accounts
   - Rotate API keys regularly
   - Store certificates securely

2. **Data Protection**
   - Enable encryption at rest for sensitive data
   - Use HTTPS for all external communications
   - Regularly backup your database
   - Keep software dependencies updated

3. **Access Control**
   - Limit file system permissions
   - Use dedicated service accounts
   - Enable audit logging
   - Monitor for suspicious activity

### For Developers

1. **Code Security**
   - No secrets in code (use environment variables)
   - Sanitize all user inputs
   - Use parameterized queries (SQLAlchemy)
   - Validate file uploads
   - Implement rate limiting

2. **Dependencies**
   - Run `safety check` regularly
   - Keep dependencies updated
   - Review dependency licenses
   - Use `pip-audit` or similar tools

3. **Testing**
   - Write security tests
   - Test authentication/authorization
   - Fuzz test inputs
   - Check for common vulnerabilities (OWASP Top 10)

## Security Features

### Implemented

- ✅ **Secrets Management** - Environment variables + encryption support
- ✅ **Input Validation** - Pydantic models for data validation
- ✅ **SQL Injection Protection** - SQLAlchemy ORM (parameterized queries)
- ✅ **Audit Logging** - Structured logs with correlation IDs
- ✅ **Sensitive Data Filtering** - Automatic redaction in logs
- ✅ **HTTPS** - Required for PEC communications
- ✅ **Dependency Scanning** - GitHub Dependabot + Safety
- ✅ **Code Scanning** - Trivy security scanner in CI

### Planned

- 🔄 **Digital Signature Verification** - Verify signed XMLs
- 🔄 **Rate Limiting** - Prevent abuse
- 🔄 **2FA Support** - Two-factor authentication
- 🔄 **Secrets Rotation** - Automatic credential rotation
- 🔄 **Intrusion Detection** - Monitor for attacks

## Secure Configuration

### Minimal Secure Setup

```bash
# .env
# Use strong, unique values!

# Database (use encryption-enabled database in production)
DATABASE_URL=sqlite:///./openfatture.db

# PEC Credentials (rotate regularly)
PEC_ADDRESS=your@pec.it
PEC_PASSWORD=strong_random_password_here
PEC_SMTP_SERVER=smtp.pec.aruba.it
PEC_SMTP_PORT=465

# Encryption Key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())")
ENCRYPTION_KEY=your_base64_encryption_key_here

# AI API Keys (if using)
AI_API_KEY=sk-...  # Keep secret!
```

### Production Hardening

1. **Use PostgreSQL with SSL**
   ```bash
   DATABASE_URL=postgresql://user:pass@localhost/openfatture?sslmode=require
   ```

2. **External Secrets Manager**
   ```bash
   # Instead of .env, use:
   # - AWS Secrets Manager
   # - HashiCorp Vault
   # - Azure Key Vault
   ```

3. **Network Security**
   - Use firewall rules
   - Restrict outbound connections
   - Use VPN for sensitive operations

4. **Monitoring**
   - Enable audit logs
   - Set up alerts for suspicious activity
   - Monitor failed login attempts
   - Track API usage

## Compliance

### GDPR

OpenFatture handles personal data (client information, financial data). Ensure:

- ✅ Data minimization - Only collect necessary data
- ✅ Right to access - Users can export their data
- ✅ Right to deletion - Users can delete their data
- ✅ Data encryption - Sensitive data encrypted
- ✅ Audit logs - Track all data access
- ✅ Data retention - 10-year retention for invoices (Italian law)

### Italian Tax Law

- ✅ Invoice data stored for 10 years
- ✅ Audit trail for all operations
- ✅ Tamper-proof logs
- ✅ SDI communication logs

## Security Checklist

### Before Production

- [ ] Change all default passwords
- [ ] Enable encryption at rest
- [ ] Set up backup system
- [ ] Configure secrets manager
- [ ] Enable audit logging
- [ ] Set up monitoring/alerting
- [ ] Review file permissions
- [ ] Enable HTTPS everywhere
- [ ] Test disaster recovery
- [ ] Review security policy with team
- [ ] Conduct security audit
- [ ] Test incident response plan

### Regular Maintenance

- [ ] Update dependencies (monthly)
- [ ] Rotate secrets (quarterly)
- [ ] Review access logs (weekly)
- [ ] Test backups (monthly)
- [ ] Security scan (continuous)
- [ ] Review audit logs (weekly)
- [ ] Update firewall rules (as needed)

## Known Limitations

1. **Digital Signatures** - Currently requires external tools
2. **Multi-tenancy** - Not yet supported (use separate instances)
3. **API Rate Limiting** - Not implemented (use reverse proxy)

## Contact

- Security issues: info@gianlucamazza.it
- General support: info@gianlucamazza.it
- GitHub Issues: https://github.com/gianlucamazza/openfatture/issues

---

Last updated: 2025-01-09
