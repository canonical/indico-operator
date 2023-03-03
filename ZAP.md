# ZAP - Ignored Alerts

## 10202   IGNORE  (Absence of Anti-CSRF Tokens)

By design, Indico doesn’t add csrf token to unauthenticated access.

## 10031   IGNORE  (User Controllable HTML Element Attribute (Potential XSS))

Indico returns a "Bad Request" error in case of malformed input.

## 10049-3 IGNORE  (Storable and Cacheable Content)

The response does not contain sensitive, personal or user-specific information.

## 10049-3 IGNORE  (Sub Resource Integrity Attribute Missing)

To be worked.

## 10109    IGNORE  (Modern Web Application)

The Ajax Spider scan is not a good fit for the integration test.

## 90033    IGNORE  (Loosely Scoped Cookie)

Specifying Domain is less restrictive than omitting it.
Read more about in [Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies).

## 10049-1 IGNORE  (Non-Storable Content)

The response contains sensitive, personal or user-specific information.

## 10027   IGNORE  (Information Disclosure - Suspicious Comments)

The comments does not contain sensitive information.

## 10054   IGNORE  (Cookie without SameSite Attribute)

We are not setting this one because "The cookie-sending behavior if SameSite is not specified is SameSite=Lax. Previously the default was that cookies were sent for all requests."
Read more about int [SameSite](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
