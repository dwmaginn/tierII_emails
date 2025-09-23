import base64

# The base64 content from the debug output
base64_content = "SGkgSm9zw6ksCgpJIGhvcGUgdGhpcyBlbWFpbCBmaW5kcyB5b3Ugd2VsbC4gSSdtIERhdmlkIGZyb20gSG9uZXN0IFBoYXJtY28sIGFuZCBJIHdhbnRlZCB0byByZWFjaCBvdXQgdG8geW91IHBlcnNvbmFsbHkuCgpXZSd2ZSBiZWVuIHdvcmtpbmcgb24gc29tZSBleGNpdGluZyBkZXZlbG9wbWVudHMgaW4gcGhhcm1hY2V1dGljYWwgcmVzZWFyY2gsIGFuZCBJIGJlbGlldmUgeW91IG1pZ2h0IGZpbmQgdGhlbSBpbnRlcmVzdGluZy4KCkJlc3QgcmVnYXJkcywKRGF2aWQKSG9uZXN0IFBoYXJtY28="

# Decode the base64 content
decoded_bytes = base64.b64decode(base64_content)
decoded_text = decoded_bytes.decode('utf-8')

print("Decoded content:")
print(repr(decoded_text))
print("\nReadable content:")
print(decoded_text)
print("\nChecking for 'Hi José,':")
print("'Hi José,' in decoded_text:", 'Hi José,' in decoded_text)