# ZAP - Ignored Alerts

## 10202   IGNORE  (Absence of Anti-CSRF Tokens)

By design, Indico doesn’t add csrf token to unauthenticated access.

## 10031   IGNORE  (User Controllable HTML Element Attribute (Potential XSS))

Indico returns a "Bad Request" error in case of malformed input.

## 10049-3 IGNORE  (Storable and Cacheable Content)

The response does not contain sensitive, personal or user-specific information so is OK to be cached.

## 10049-3 IGNORE  (Sub Resource Integrity Attribute Missing)

SRI is mostly used in assets served by CDN, in this case the assets are served directly from our server.

## 10109    IGNORE  (Modern Web Application)

The Ajax Spider scan is not a good fit for the integration test.

## 90033    IGNORE  (Loosely Scoped Cookie)

Specifying Domain is less restrictive than omitting it.
Read more about it in [Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies).

## 10049-1 IGNORE  (Non-Storable Content)

This alert is being raised for paths /admin and /rooms because Indico redirects to /admin/settings and /rooms/book.
There is no action regarding cache to do about it since the redirect is expected.

## 10027   IGNORE  (Information Disclosure - Suspicious Comments)

The comments do not contain sensitive information.

## 10054   IGNORE  (Cookie without SameSite Attribute)

We are not setting this one because "The cookie-sending behavior if SameSite is not specified is SameSite=Lax.
Previously the default was that cookies were sent for all requests."
Read more about it in [SameSite](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite).

## 10110   IGNORE  (Dangerous JS Functions)

False positive by getting "eval" string.

More information in [eval](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/eval).

## 10063-1 IGNORE  (Permissions Policy Header Not Set)

Permissions are features offered by the browser through an API. You have to specify every permission separately, so setting a value for this header could negatively impact the user experience.

More information in [Permissions Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy).

## 10038   IGNORE   (Content Security Policy (CSP) Header Not Set)

By enabling CSP Header, some features while creating events don't work as expected so we are ignoring this alert.
