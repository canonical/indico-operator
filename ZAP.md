# ZAP - Ignored Alerts

## 10202   IGNORE  (Absence of Anti-CSRF Tokens)

By design, Indico doesn’t add csrf token to unauthenticated access.

## 10031   IGNORE  (User Controllable HTML Element Attribute (Potential XSS))

Indico returns a "Bad Request" error in case of malformed input.

## 10049-3 IGNORE  (Storable and Cacheable Content)

Managed by request header Cache-Control 'no-cache,private'.