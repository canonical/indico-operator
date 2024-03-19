<!-- markdownlint-disable -->

<a href="../src/state.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `state.py`
Indico states. 



---

## <kbd>class</kbd> `CharmConfigInvalidError`
Exception raised when a charm configuration is found to be invalid. 



**Attributes:**
 
 - <b>`msg`</b>:  Explanation of the error. 

<a href="../src/state.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the CharmConfigInvalidError exception. 



**Args:**
 
 - <b>`msg`</b>:  Explanation of the error. 





---

## <kbd>class</kbd> `CharmStateBaseError`
Represents an error with charm state. 





---

## <kbd>class</kbd> `ProxyConfig`
Configuration for accessing Indico through proxy. 



**Attributes:**
 
 - <b>`http_proxy`</b>:  The http proxy URL. 
 - <b>`https_proxy`</b>:  The https proxy URL. 
 - <b>`no_proxy`</b>:  Comma separated list of hostnames to bypass proxy. 




---

<a href="../src/state.py#L53"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_env`

```python
from_env() → Optional[ForwardRef('ProxyConfig')]
```

Instantiate ProxyConfig from juju charm environment. 



**Returns:**
  ProxyConfig if proxy configuration is provided, None otherwise. 


---

## <kbd>class</kbd> `SamlConfig`
SAML configuration. 



**Attributes:**
 
 - <b>`entity_id`</b>:  SAML entity ID. 
 - <b>`metadata_url`</b>:  Metadata URL. 
 - <b>`certificates`</b>:  List of x509 certificates. 
 - <b>`endpoints`</b>:  List of endpoints. 





---

## <kbd>class</kbd> `SamlEndpoint`
SAML configuration. 



**Attributes:**
 
 - <b>`name`</b>:  Endpoint name. 
 - <b>`url`</b>:  Endpoint URL. 
 - <b>`binding`</b>:  Endpoint binding. 
 - <b>`response_url`</b>:  URL to address the response to. 





---

## <kbd>class</kbd> `SmtpConfig`
SMTP configuration. 



**Attributes:**
 
 - <b>`login`</b>:  SMTP user. 
 - <b>`password`</b>:  SMTP passwaord. 
 - <b>`port`</b>:  SMTP port. 
 - <b>`host`</b>:  SMTP host. 
 - <b>`use_tls`</b>:  whether TLS is enabled. 





---

## <kbd>class</kbd> `State`
The Indico operator charm state. 



**Attributes:**
 
 - <b>`proxy_config`</b>:  Proxy configuration. 
 - <b>`saml_config`</b>:  SAML configuration. 
 - <b>`smtp_config`</b>:  SMTP configuration. 




---

<a href="../src/state.py#L136"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_charm`

```python
from_charm(
    charm: CharmBase,
    saml_relation_data: Optional[SamlRelationData] = None,
    smtp_relation_data: Optional[SmtpRelationData] = None
) → State
```

Initialize the state from charm. 



**Args:**
 
 - <b>`charm`</b>:  The charm root IndicoOperatorCharm. 
 - <b>`saml_relation_data`</b>:  SAML relation data. 
 - <b>`smtp_relation_data`</b>:  SMTP relation data. 



**Returns:**
 Current state of Indico. 



**Raises:**
 
 - <b>`CharmConfigInvalidError`</b>:  if invalid state values were encountered. 


