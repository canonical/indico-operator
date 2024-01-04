<!-- markdownlint-disable -->

<a href="../src/charm.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm.py`
Charm for Indico on kubernetes. 

**Global Variables**
---------------
- **CELERY_PROMEXP_PORT**
- **DATABASE_NAME**
- **EMAIL_LIST_MAX**
- **EMAIL_LIST_SEPARATOR**
- **INDICO_CUSTOMIZATION_DIR**
- **NGINX_PROMEXP_PORT**
- **PORT**
- **STATSD_PROMEXP_PORT**
- **UBUNTU_SAML_URL**
- **STAGING_UBUNTU_SAML_URL**
- **SAML_GROUPS_PLUGIN_NAME**
- **UWSGI_TOUCH_RELOAD**


---

## <kbd>class</kbd> `IndicoOperatorCharm`
Charm for Indico on kubernetes. 

Attrs:  on: Redis relation charm events. 

<a href="../src/charm.py#L57"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(*args)
```

Construct. 



**Args:**
 
 - <b>`args`</b>:  Arguments passed to the CharmBase parent constructor. 


---

#### <kbd>property</kbd> app

Application that this unit is part of. 

---

#### <kbd>property</kbd> charm_dir

Root directory of the charm as it is running. 

---

#### <kbd>property</kbd> config

A mapping containing the charm's config and current values. 

---

#### <kbd>property</kbd> meta

Metadata of this charm. 

---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 

---

#### <kbd>property</kbd> unit

Unit that this execution is responsible for. 




