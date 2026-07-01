#!/usr/bin/env python
"""
EMAIL SETUP GUIDE FOR GMAIL
"""

print("📧 FALL DETECTION SYSTEM - EMAIL SETUP GUIDE")
print("="*60)

print("\n❌ CURRENT STATUS: Email authentication failed")
print("   Error: Gmail requires App Password for SMTP access")
print("   Your current App Password may be invalid or expired")

print("\n🔧 TO FIX THIS - Follow these steps:")
print("\n1. ENABLE 2-FACTOR AUTHENTICATION:")
print("   • Go to: https://myaccount.google.com/security")
print("   • Sign in to your Gmail account (kishore5758s@gmail.com)")
print("   • Enable 2-Step Verification if not already enabled")

print("\n2. GENERATE A NEW APP PASSWORD:")
print("   • Go to: https://myaccount.google.com/apppasswords")
print("   • Sign in if prompted")
print("   • Select 'Mail' from the dropdown")
print("   • Select 'Windows Computer' or create custom name")
print("   • Click 'Generate'")
print("   • COPY the 16-character password (remove all spaces)")
print("   • Example: 'abcd efgh ijkl mnop' → 'abcdefghijklmnop'")

print("\n3. UPDATE YOUR .env FILE:")
print("   • Open .env file in your project folder")
print("   • Change EMAIL_PASS to your new App Password:")
print("   • EMAIL_PASS=abcdefghijklmnop")
print("   • Save the file")

print("\n4. RESTART AND TEST:")
print("   • Close and reopen your terminal/command prompt")
print("   • Run: python test_email.py")
print("   • Check if you receive the test email at ksanjuma1234@gmail.com")

print("\n📧 ALTERNATIVE: Use a different email provider")
print("   • Outlook: smtp-mail.outlook.com:587")
print("   • Yahoo: smtp.mail.yahoo.com:587")
print("   • Update email_service.py with your provider settings")

print("\n🔍 TROUBLESHOOTING:")
print("   • Make sure you're using the correct Gmail account")
print("   • App Password should be exactly 16 characters, no spaces")
print("   • Try generating a fresh App Password")
print("   • Check Gmail for security alerts")

print("\n✅ ONCE WORKING: The system will send alerts to ksanjuma1234@gmail.com")
print("   when falls are detected!")

print("\n" + "="*60)
