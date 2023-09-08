<!-- markdownlint-disable -->

<a href="../src/database_observer.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `database_observer.py`
The Database agent relation observer. 



---

## <kbd>class</kbd> `DatabaseObserver`
The Database relation observer. 

Attrs:  uri: The database uri. 

<a href="../src/database_observer.py#L28"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase)
```

Initialize the observer and register event handlers. 



**Args:**
 
 - <b>`charm`</b>:  The parent charm to attach the observer to. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 

---

#### <kbd>property</kbd> uri

Get the database uri from the relation data. 



**Returns:**
 
 - <b>`str`</b>:  The uri. 




