# Examples

## Commands

Here are some example commands that can be used as a reference when writing your own.

### Run Python script within virtualenv

Shows example of executing `update-script.py` from within a virtualenv.

```yaml
update_command:
  - /path/to/project/.venv/bin/python
  - /path/to/project/update-script.py
```

### Update README copyright year

This update command will leverage [sed](https://www.gnu.org/software/sed/manual/sed.html) to update the copyright year of all the `README.md` files.

```yaml
...
update_command:
- sed
- -i
- 's/Copyright [0-9]\+/Copyright 2021/g'
- README.md
```
