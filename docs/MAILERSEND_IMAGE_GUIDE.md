# MailerSend Image Embedding Guide

## Template Update Complete
The `wholesale_template.html` has been updated to include the Honest Pharmco logo image in place of the text header.

## Image Implementation
- **Template Change**: Replaced `<h1 class="company-name">Honest Pharmco</h1>` with `<img src="cid:hpc_logo" alt="Honest Pharmco" class="company-logo" />`
- **CSS Updates**: Added responsive styling for the logo image
- **CID Reference**: Using `cid:hpc_logo` for MailerSend compatibility

## Using with MailerSend API

### Method 1: CID Attachment (Recommended)
When sending emails through MailerSend API, attach the image file and reference it using the CID:

```javascript
// Example with MailerSend SDK
const attachment = {
  content: base64EncodedImage, // or file buffer
  filename: "hpc_transparent.png",
  type: "image/png",
  disposition: "inline",
  id: "hpc_logo" // This matches the CID reference in template
};
```

### Method 2: Hosted Image
1. Upload `hpc_transparent.png` to a web server
2. Replace `cid:hpc_logo` with the full URL: `https://yourdomain.com/images/hpc_transparent.png`

### Method 3: Base64 Inline (Not Recommended)
Replace `cid:hpc_logo` with a base64 data URI, but note this increases email size significantly.

## Template Features
- **Responsive Design**: Logo scales down to 150px on mobile devices
- **Accessibility**: Includes proper alt text
- **Centered Layout**: Maintains the original design alignment
- **Email Client Compatible**: Uses standard HTML img tag

## Next Steps
1. Test the template with your MailerSend integration
2. Ensure the image attachment is properly configured in your email sending code
3. Verify rendering across different email clients