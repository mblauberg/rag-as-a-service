# Security Policy

## Project Status

**Note**: This is a portfolio and academic project. It is not actively maintained for production use.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

### For Educational/Portfolio Context

1. **Open a GitHub Issue** using the bug report template
2. Clearly mark it with the `security` label
3. Describe the vulnerability and potential impact
4. If possible, include steps to reproduce

### For Private Disclosure

If you prefer to report security issues privately:

1. Email: mblauberg@outlook.com
2. Include "SECURITY" in the subject line
3. Provide detailed information about the vulnerability
4. Allow 48-72 hours for response

## Security Considerations

### Known Limitations

This project is designed for **demonstration and learning purposes**. Before deploying in any production environment, consider:

1. **API Key Management**
   - Never commit API keys to version control
   - Use proper secret management (Kubernetes Secrets, HashiCorp Vault)
   - Rotate keys regularly

2. **Authentication & Authorization**
   - Current implementation has no user authentication
   - No authorization controls on document access
   - Recommended: Add OAuth2/JWT before production use

3. **Input Validation**
   - File upload size limits are configurable
   - Content type validation is basic
   - Consider additional malware scanning for production

4. **Rate Limiting**
   - No built-in rate limiting
   - Add reverse proxy with rate limiting (NGINX, Traefik) for production

5. **Database Security**
   - Default credentials in docker-compose should be changed
   - Use TLS for database connections in production
   - Implement proper backup and recovery procedures

6. **Network Security**
   - Services communicate over internal Docker network
   - In production, use network policies and service mesh
   - Enable TLS for all external communications

## Security Best Practices Implemented

- ✅ Environment variables for sensitive configuration
- ✅ Docker multi-stage builds (reduced attack surface)
- ✅ Health checks and automatic restarts
- ✅ Pydantic validation for all API inputs
- ✅ Async/await to prevent blocking attacks
- ✅ Type safety (Python type hints + TypeScript)
- ✅ Dependency scanning via Poetry and npm

## Dependencies

### Monitoring for Vulnerabilities

```bash
# Python dependencies
cd services/api && poetry show --outdated
poetry audit  # Using poetry-audit-plugin

# Node.js dependencies
cd services/frontend && npm audit
```

### Update Process

Dependencies are managed via:
- Python: `pyproject.toml` with version constraints
- Node.js: `package.json` with locked versions (`package-lock.json`)

## Responsible Disclosure

This project is open source and educational. If you find security issues:

1. Responsible disclosure is appreciated
2. Credit will be given for valid findings
3. Allow time for fixes before public disclosure

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)

---

**Disclaimer**: This is a demonstration project. Use at your own risk.
