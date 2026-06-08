# Sign Server Config Reference

## Docker container: bennettwu/qsign-server:latest

Location: `/app/txlib/config.json` (inside container)

## Default config (auto_register=false)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 80
  },
  "share_token": true,
  "count": 10,
  "key": "114514",
  "auto_register": false,
  "protocol": {
    "package_name": "com.tencent.mobileqq",
    "qua": "V1_AND_SQ_8.9.63_4194_YYB_D",
    "version": "8.9.63",
    "code": "4194"
  },
  "unidbg": {
    "dynarmic": false,
    "unicorn": true,
    "kvm": false,
    "debug": false
  }
}
```

## After fix (auto_register=true)

```json
{
  ...
  "auto_register": true,
  ...
}
```

## Available protocols (inside container)

```
docker exec <container> ls /app/txlib/
```

Typical output:
```
3.5.1   3.5.2   8.9.63   8.9.68   8.9.71   8.9.73   8.9.80   config.json   dtconfig.json   libfekit.so
```

All are Android protocols. No MacOS/iOS/Windows protocols available.

## Key notes

- `auto_register: true` allows the sign server to accept new QQ UINs that it hasn't seen before
- `share_token: true` means the same token can be reused across sessions (until expiry)
- `count: 10` limits simultaneous instances
- `key: "114514"` — shared secret between go-cqhttp and sign server, must match in both configs
- unidbg backend: `unicorn: true` (default), optionally switch to `dynarmic: true` for performance on ARM
