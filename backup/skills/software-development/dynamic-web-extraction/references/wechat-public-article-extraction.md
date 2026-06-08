Archived source skill: wechat-public-article-extraction

This reference preserves the absorbed content-extraction patterns:
- try direct curl with mobile UA first
- detect verification pages instead of trusting HTTP 200
- use browser evaluate/DOM extraction only when needed
- normalize output into title/author/publish/body/page-type fields
- note that browser automation may hit anti-bot where plain fetch succeeds

The original skill and any support files are preserved in ~/.hermes/skills/.archive.