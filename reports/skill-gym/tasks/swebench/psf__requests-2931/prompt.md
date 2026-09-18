You are working in a checkout of psf/requests at commit 5f7a3a74aab1.
The project's virtualenv (.venv) is installed (editable) and already activated:
`python` and `pytest` on PATH are the project's own.

Below is a real GitHub issue for this repository. Fix it.

Rules:
- Modify source code only. Do NOT modify any test files.
- Work only from this checkout. Do NOT download, install or consult any other copy
  or later version of this project (no pip/curl/git fetches of upstream code), and
  do not read files outside this directory apart from your own scratch files.
- Verify your fix by running relevant tests before finishing.
- When done, summarize the root cause and your change.

<issue>
Request with binary payload fails due to calling to_native_string
Introduced with https://github.com/kennethreitz/requests/issues/2844

```
import requests
requests.put("http://httpbin.org/put", data=u"ööö".encode("utf-8"))
```

This works with 2.8.1, but not with 2.9.
</issue>
