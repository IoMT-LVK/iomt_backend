# Secrets directory

Here place your secrets

List of needed files:
- db\_password.txt
  > If you ever want to change db\_password, don't forget to change it manually in MySQL container.
  > User password initialized only in first run.
- mail\_password.txt - your email account password for registration emails.
- jwt\_key.txt - (random) just set of bytes for encoding JWT
- email\_jwt\_key.txt - (random) another set of bytes
- root\_operator\_password.txt - passsword for root operator

**Note: for generating random string you can use mktemp**
```
mktemp --dry-run XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX > jwt_key.txt
```
